# restaurant-scraper
Con lo scopo di ottenere le informazioni relative ai ristoranti della città di Milano e relative review, è utilizzata la combinazione Selenium - BeautifulSoup. Il primo permette di automatizzare il caricamento e lo scorrimento delle pagine di ristoranti e review, il secondo permette l'interpretazione e la navigazione nell'HTML della pagina caricata.

## Approccio ad alto livello
Partendo dall'URL della ricerca dei ristoranti a Milano (https://www.tripadvisor.it/Restaurants-g187849-Milan_Lombardy.html), la procedura è divisa in due step:
1) Identificazione del perimetro
2) Scraping di ristoranti e recensioni

L'approccio in due step permette di avere nella prima fase: 
In input dei criteri secondo i quali selezionare o meno lo specifico ristorante, in output la lista di ristoranti di cui andare a salvare le informazioni.

Dato il meccanismo di ranking dei risultati intrinseco nella piattaforma Tripadvisor, raccogliendo semplicemente i primi 1000 ristoranti si sarebbe ottenuto un dataset sbilanciato verso valutazioni molto positive (5 o 4.5 stelle).
E' stato necessario quindi imporre dei vincoli nella fase di definizione del perimetro. I criteri scelti sono stati:
- Un minimo totale di ristoranti raccolti (di default 1000)
- Un minimo di ristoranti per ogni numero di stelle (di default 25)
- Un massimo di ristoranti per ogni numero di stelle (250)
- Un minimo di recensioni per il ristorante (25)
Durante lo scorrimento dei risultati ogni singolo ristorante è valutato contro i criteri sopra citati, e se rientrante in tutti i vincoli è aggiunto al perimetro.

Nella seconda fase, invece:
In input la lista dei ristoranti precedemente ricavata (eventualmente sezionata), in output ristoranti con informazioni e relative review.

Data la lista di ristoranti ottenuta nel primo step, la seconda fase è quella dello scraping vero e proprio. Ogni URL della lista dei ristoranti nel perimetro viene caricato, salvando tutte le informazioni del ristorante. Vengono poi caricate tre pagine di recensioni (10 recensioni ognuna), le cui informazioni sono salvate (dopo aver espanso i commenti compressi).
Tutte le informazioni sono scritte su due file CSV di appoggio (sep='|', avendo cura di rimuovere il carattere dai commenti), per poi essere caricati su un database (SQLite). La soluzione scelta emula un contesto reale, in cui si lavora il batch in locale, per poi aprire una connessione ad un database (analitico) per il caricamento del batch stesso. Un'opzione alternativa sarebbe potuta essere la scrittura su un database (transazionale) direttamente durante lo scraping.

## Implementazione tecnica
Per implementare quanto descritto sopra, è stato deciso di adottare l'approccio object oriented, creando una semplice classe contenente tutti i metodi necessari.
La classe (AdvisorScraper) viene istanziata prendendo in input due path fondamentali: la posizione dei dati utente, la posizione dell'eseguibile (chromedriver).
Alla sua inizializzazione viene istanziato il driver Chrome, passando le opzioni dei dati utenti assegnate e passando il path dell'eseguibile (_instantiate_driver(), tutti i metodi ad uso interno della classe sono definiti con prefisso underscore).

Il metodo perimeter_definition() corrisponde a quanto descritto nel primo step della sezione precedente.
Prende come parametri di input l'URL da cui partire per la ricerca e per scorrere le pagine, un minimo totale di review (settato di default a 1000), un minimo per ogni rank (settato di defautl a 25), e una stringa corrispondente al nome del file di output (di defatul 'perimeter.txt').
Vengono definiti due dizionari di appoggio. Il primo (perimeter_dictionary) conterra le coppie chiave:valore corrispondenti a URL:rank. E' scelto il dizionario in quanto permette di default di evitare duplicati sulle chiavi (URL), che sono inoltre hashate.
Il secondo dizionario contiene le coppie rank:numero di ristoranti salvati, per permettere di tenere il conto dei ristoranti per rank (minimo 25 massimo 250).
Il ciclo while continua finché si verificano due condizioni: il perimetro è minore del numero minimo di ristoranti da ottenere (1000), almeno uno dei conteggi dei ristoranti per rank è minore del minimo di ristoranti per rank (25). I.e. Dal momento in cui si superano 25 ristoranti per rank & si supera un totale di 1000 ristoranti, si esce dal ciclo ed il perimetro è completo.
Ogni step in cui si carica una pagina web è racchiuso all'interno di try-except, per permettere al processo di essere robusto contro diversi livelli di errore. Ogni eccezione è raccolta come eccezione generica, anche se non una best practice, nel contesto attuale non interessa approfondire ulteriormente.
Ogni "soup" (oggetto che interpreta l'HTML) è definito con la funzione _get_soup(), alla quale viene passato l'URL da cui fare lo scraping. Essa richiama a sua volta il metodo _load_page_and_wait(), che carica la pagina ed aspetta un tempo casuale uniforme tra 1.5 e 2.5 secondi, per evitare ban e rendere lo scraper meno facilmente intercettabile dall'antibot. 
Dalla soup vengono presi tutti i box (i rettangoli contenti i ristoranti nella pagina risultati), che vengongo ciclati nel for.
Una guard (il primo if), permette di skippare il box se il ristorante è sponsorizzato.
Vengono poi assegnati numero di review, url e rank, ritornati dal metodo _scrape_restaurant_box(), che prende in input la soup del box stesso. Questa, al suo interno, non fa altro che cercare i vari elementi di interesse tramite .find all'interno della soup, che sono poi lavorati tramite metodi vari (ex: split o replace) per renderli nel formato desiderato.
Tornando nel for, altre due guard sono presenti per skippare il ristorante se ha meno di 25 review o se il suo rank ha superato il 250 ristoranti nel perimetro (ex: 250 ristoranti da 4 stelle, skippo quello che sarebbe il 251esimo ristorante da 4 stelle).
Passati i due if, la coppia ristorante:rank viene aggiunta al primo dizionario di appoggio, e il conteggio del rank viene innalzato di 1 nel secondo dizionario di appoggio.
Una volta fuori dal for (ovvero finiti i box dei ristoranti nella pagina), viene assegnato un nuovo search_url che corrisponde a quello del tasto della pagina successiva (metodo _get_next_page(), che ritorna False se la pagina successiva non esiste, il quale False permette di uscire dal while, chiudendo il perimetro).
Qualunque erorre a livello di box viene intercettato skippando il box, qualunque errore a livello di pagina viene intercettato skippando la pagina.
Il perimetro viene poi salvato su un file (metodo _perimeter_to_file()), dove vengono scritti URL|rank, nell'ipotesi di dividere per rank tra diversi device lo step di scraping successivo.
La lista degli url viene poi assegnata alla variabile d'istanza perimeter_list, e infine ritornata dal metodo per ulteriori utilizzi.

Il metodo scrape_entity_review() è l'esecuzione vera e propria dello scraping.
Al suo interno viene assegnata la lista degli url variabile di istanza, solo se non passata come parametro all'invocazione del metodo stesso.
Vengono aperti in due context due file di appoggio in write per scrivere le due intestazioni, e vengono poi aperti di nuovo in append.
Partono quindi tre cicli for annidati uno dentro l'altro, con relativi try-except per intercettare errori e skippare ristoranti/review che li causano.
Il for più esterno scorre la lista degli URL ottenendo la soup di ogni ristorante.
Questa viene poi passata al metodo _scrape_restaurant(), che raccoglie tutte le informazioni necessarie (nome, indirizzo, etc.), per poi ritornarle in una lista. La lista viene appiattita e scritta sul file restaurant.txt, sempre con separatore '|'. Per ogni testo raccolto, vengono rimossi '|' e vari newline.
Il secondo for scorre invece le pagine delle review. Ogni pagina contiene 10 review. La soup viene ottenuta con la funzione _load_expand_and_get_soup(), che prima di scrapare l'html attende il caricamenteo del tasto "Più", e se presente lo clicca, per espandere il testo delle review.
Viene poi definita una stringa vuota di appoggio, sulla quale si va in append con le varie review, raccolte all'interno del terzo ciclo for. In modo analogo ai ristoranti, il metodo _scrape_review() raccoglie le informazioni e le ritorna come lista, la quale viene poi appiattita e messa in append alla stringa vuota. Dopo aver raccolto le 10 review della pagina, la stringa viene scritta sul relativo file.
I due file vengono flushati ad ogni ristorante/ogni 10 review.
Una volta usciti dal ciclo for più esterno (ovvero finiti i ristoranti), i due file vengono chiusi.
L'ultimo metodo permette la chiusura del driver.

Lo scraper viene istanziato, e i due metodi richiamati, nel main.py.

## Salvataggio dei dati
Dato il caso molto semplice, è utilizzato un notebook (load_to_db.ipynb) per aprire una connessione ad un database sqlite (advisor.db), creare due tabelle per ristoranti e review, e caricarvi i dati letti dai CSV via Pandas.
