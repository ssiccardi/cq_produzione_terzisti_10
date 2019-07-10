==========================================================
MRP contractors' management, for Odoo rel.10 community ed.
==========================================================

=============================================
Gestione della produzione conto terzi, rel.10
=============================================

Gestione terzisti tramite 2 modalità:

* **alla NT**: gestita tramite scheduler e regole riordino
* **alla JG**: automatizzata tramite routings (caso MakeToOrder)

Il modulo supporta anche distinte base su varianti, con la sola restrizione che la modalità
di lavorazione terzista (campo *Tipo gestione terzista*) è selezionabile solo sul template.

**TO-DO AL MOMENTO DELL'INSTALLAZIONE SUI DB CLIENTI**

L'idea di fondo del modulo è che per ogni installazione/cliente
venga scelta una delle 2 modalità in modo "permanente" (come quando si sceglie di usare o meno le varianti).
Sarebbe bene nascondere la modalità non usata, modificando la selezione del campo *terz_type* di *product.template*
direttamente nel python del modulo di personalizzazione del cliente 

Vedere in fondo, nella sezione Roadmap, possibili miglioramenti per facilitare l'utilizzo.

-------------
Menu aggiunti
-------------

Inventario / Movimenti verso terzisti: raccoglie tutti gli OUT verso terzisti e collegati a ordini produzione.
È possibile il trasferimento simultaneo di vari OUT selezionando le righe > Azione > Trasferimento Movimenti.

-----------------------
Configurazione generale
-----------------------

Per entrambe le modalità è necessario:

* avere dei **fornitori** che fungono da terzisti
* avere un **punto di stoccaggio interno** per ogni terzista; il campo Proprietario DEVE essere compilato


-----------
Modalità NT
-----------

* Consigliata nel caso di produzione MTS o si necessiti inviare la merce a molti terzisti
* L'OUT di invio merce al terzista è collegato all'ordine di produzione svolta dal terzista.
* Nel caso di distinte base *verticali* (ovvero annidate su più livelli),
    potrebbe essere necessario far girare lo scheduler più volte per creare
    tutti gli ordini di produzione necessari a completare i passaggi della distinta finale.

**Esempio di distinta, prodotto A / variante varA:**

* prodotto *A* --> distinta *A/varA*, composta da:
    - prodotto *a1*
    - prodotto *a2*
    - ...

^^^^^^^^^^^^^^^^^
Configurazione NT
^^^^^^^^^^^^^^^^^

* Scheda template di *A*
    - campo **Tipo gestione terzista**: "Lavorato da terzista"
    - campo **Luogo Terzista**: punto stoccaggio del terzista scelto
    - campo **Punto sped. terzista**: punto stoccaggio di ritorno della merce dal terzista
    - campo **Percorsi**: "Produci"
    - regole riordino: una regola per il punto di stoccaggio interno usato solitamente per prelevare la merce nella produzione (es. WH/Stock)

* componenti *a1*, *a2* ...
    - NON è necessario il campo **Tipo gestione terzista**: "Spedito al terzista"
    - solite regole riordino nel caso di acquisto o produzione MTS o MTO per Stock
    - NO regole riordino per punto di stoccaggio del terzista (altrimenti cerca le regole di approvvigionamento)

^^^^^^^^^^
Esecuzione
^^^^^^^^^^

L'ordine di produzione sulla variante *varA* riporta:
* il campo *Tipo gestione terzista*: *Lavorato da terzista*
* il campo *Ubicazione materie prime*: campo *Luogo Terzista* sul template *A*

- sulla schedina "Spedizione verso terzista" cliccare il bottone **Spedisci materie Prime** in cui scegliere da dove prelevare le componenti
- questo crea un OUT verso il proprietario dello stoccaggio scelto su *Ubicazione materie prime*
- trasferire l'OUT


-----------
Modalità JG
-----------

* Consigliata nel caso di produzione MTO oppure si abbiano distinte verticali a molti passaggi
* Rende minima la parte di configurazione per l'utente e non bisogna usare lo scheduler
* Sconsigliata nel caso si necessiti inviare la merce a molti terzisti o si voglia avere una gestione più dinamica della produzione
* Necessita una coppia di routing "spedisci/produci" per ogni terzista
* L'OUT di invio merce al terzista è collegato all'ordine di produzione del prodotto da inviare al terzista


**Esempio di distinta annidata, prodotto A / variante varA:**

* prodotto *A* --> distinta *A/varA*, composta da:
    - prodotto *B* --> distinta *B/varB*, composta da: (da fare presso terzista)
        - prodotto *C* --> distinta *C/varC*, composta da: (da spedire al terzista)
            - prodotto *c1*
            - prodotto *c1*
            - ...

^^^^^^^^^^^^^^^^^
Configurazione JG
^^^^^^^^^^^^^^^^^

Occorre creazione una coppia di routing "spedisci / produci" per ogni terzista.
Andare in Inventario > Percorsi > Percorsi

* creazione percorso *Porta al Terzista*:
    - applica a "Prodotti"
    - regola approvvigionamento *Porta al terzista* con:
        - azione: "sposta da altra location"
        - Propagazione del Gruppo di Approvvigionamento: "propaga"
        - punto approvvigionamento: stoccagio del terzista
        - magazzino servito: WH
        - ubicazione provevienza: WH/Stock o simile
        - Sposta Metodo di Approvvigionamento: Crea Approvvigionamento
        - tipo picking: ordine di consegna

* creazione percorso *Produci da Terzista*:
    - applica a "Prodotti"
    - regola approvvigionamento *Porta al terzista* con:
        - azione: "produci"
        - Propagazione del Gruppo di Approvvigionamento: "propaga"
        - punto approvvigionamento: WH/Stock o simili
        - magazzino servito: WH
        - ubicazione provevienza: stoccagio del terzista
        - tipo picking: produzione (o un tipo picking 'produzione' creato appositamente)


* componenti *c1*, *c2* ...
    - solite regole riordino nel caso di acquisto o produzione MTS o MTO

* Scheda template di *C*
    - campo **Tipo gestione terzista**: "Spedito al terzista"
    - campo **Percorsi**: "Produci", "Produrre su Ordine", "Spedisci al terzista"
    - regole riordino: nessuna

* Scheda template di *B*
    - campo **Percorsi**: "Produrre su Ordine", "Produci da terzista"
    - regole riordino: nessuna

* Scheda template di *A*
    - campo **Percorsi**: "Produci"
    - regole riordino: nessuna

^^^^^^^^^^
Esecuzione
^^^^^^^^^^

La creazione dell'ordine di produzione sulla variante *varA* crea istantanemente i passaggi precedenti e prepara l'OUT verso il terzista.
L'ordine di produzione sulla variante *varC* riporta:

* il campo *Tipo gestione terzista*: *Spedito al terzista*
* schedina "Spedizione verso terzista" con l'OUT verso il terzista

Occorre:

* completare il MO per *varC*
* andare in Inventario / Movimenti verso Terzista, cercare l'OUT e trasferirlo
* ora la merce per il MO di *varB* è disponibile e si può procedere con la produzione


--------------------
Roadmap / Desiderata
--------------------

* Possibilità di selezionare la modalità di utilizzo del modulo tramite impostazioni globali.
  L'idea è di avere aggiungere un campo nella sezione Configurazione di Produzione, in modo che,
  una volta stabilita la modalità di utilizzo per il cliente, a seconda della scelta vengano
  resi invisibili o modificate certe parti (come la scelta di varianti prodotto), evitando di avere
  interferenze con le funzionalità della modalità da non usare.
  Esempi:
  
  - nascondere una delle due opzioni del campo Tipo Gestione Terzista sui prodotti
  - collegare / automatizzare la visione o meno dei percorsi "Porta/Produci Terzista" con la scelta "Spedito al terzista" sul campo Tipo Gestione Terzista
  - ...
