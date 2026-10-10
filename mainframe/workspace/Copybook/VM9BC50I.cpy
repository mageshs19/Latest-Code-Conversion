000100*    COPY-ID.           VM9BC50I.                                 00000100
000200*    DESCRIPTION.       PARAMETRES D'APPEL DU BUSINESS SERVICE.   00000200
000300*    USAGE.             COPY VM9BC50I                             00000300
000400*                         REPLACING ==:VM9BC50T:== BY ==WS==      00000400
000500*    AUTHOR.            J. DEFEYTER                               00000500
000600*    CODE-READER.                                                 00000600
000700*    CHANGED BY.                                                  00000700
000800*    DATE-WRITTEN.      23/04/2002.                               00000800
000900*    DATE-LAST-UPDATE   DD/MM/YYYY.                               00000900
001000*                                                                 00001000
001100     05  :VM9BC50T:-VM9BC50T-INPUT.                               00001100
001200     10  :VM9BC50T:-COMMON-INPUT.                                 00001200
001300         20  :VM9BC50T:-NM-CALLER                  PIC X(0008).   00001300
001400         20  :VM9BC50T:-NM-BB                      PIC X(0008).   00001400
001500         20  :VM9BC50T:-CO-TRANSMISSION            PIC X(0001).   00001500
001600         20  :VM9BC50T:-NM-FUNCTION                PIC X(0008).   00001600
001700             88  :VM9BC50T:-QUERY001         VALUE 'QUERY001'.    00001700
001700             88  :VM9BC50T:-QUERY002         VALUE 'QUERY002'.    00001710
001800     10  :VM9BC50T:-VARIABLE-INPUT.                               00001800
001900     20  :VM9BC50T:-REQUIRED-INPUT.                               00001900
002000     30  :VM9BC50T:-CO-CLE                         PIC X(001).    00002000
002100         88  :VM9BC50T:-CLE-CODE-VALEUR      VALUE '1'.           00002100
002200         88  :VM9BC50T:-CLE-NO-INTERNE       VALUE '2'.           00002200
002300         88  :VM9BC50T:-CLE-CLE-INTERNE      VALUE '3'.           00002300
002400     30  :VM9BC50T:-NR-CLE                         PIC X(016).    00002400
002500     30  FILLER REDEFINES :VM9BC50T:-NR-CLE.                      00002500
002600         32  :VM9BC50T:-NR-CLE-CODE-VALEUR         PIC X(009).    00002600
002700         32  FILLER REDEFINES :VM9BC50T:-NR-CLE-CODE-VALEUR.      00002700
002800             34  :VM9BC50T:-NR-CLE-CODE-VALEUR-B   PIC X(007).    00002800
002900             34  :VM9BC50T:-NR-CLE-CODE-VALEUR-CD  PIC X(002).    00002900
003000         32  FILLER                                PIC X(007).    00003000
003100     30  FILLER REDEFINES :VM9BC50T:-NR-CLE.                      00003100
003200         32  :VM9BC50T:-NR-CLE-NO-INTERNE          PIC X(011).    00003200
003300         32  FILLER                                PIC X(005).    00003300
003400     30 :VM9BC50T:-NR-CLE-CLE-INTERNE REDEFINES :VM9BC50T:-NR-CLE.00003400
003500         32  :VM9BC50T:-NR-PRODUIT                 PIC X(004).    00003500
003600         32  :VM9BC50T:-NS-COND-EMISSION           PIC 9(004).    00003600
003700         32  :VM9BC50T:-DA-JOUISSANCE              PIC X(008).    00003700
003800         32  FILLER REDEFINES :VM9BC50T:-DA-JOUISSANCE.           00003800
003900            34 :VM9BC50T:-DA-JOUISSANCE-YY.                       00003900
004000               36 :VM9BC50T:-DA-JOUISSANCE-Y1      PIC 9(2).      00004000
004100               36 :VM9BC50T:-DA-JOUISSANCE-Y2      PIC 9(2).      00004100
004200            34 :VM9BC50T:-DA-JOUISSANCE-M          PIC 9(2).      00004200
004300            34 :VM9BC50T:-DA-JOUISSANCE-D          PIC 9(2).      00004300
004400     20  :VM9BC50T:-OPTIONAL-INPUT.                               00004400
004500     30  :VM9BC50T:-CO-DONNEES-FIXES               PIC X(001).    00004500
004600         88  :VM9BC50T:-DONNEES-FIXES              VALUE 'Y'.     00004600
004700     30  :VM9BC50T:-CO-CONDITIONS-VENTE            PIC X(001).    00004700
004800         88  :VM9BC50T:-CONDITIONS-VENTE           VALUE 'Y'.     00004800
004900     30  :VM9BC50T:-CO-CONDITIONS-EMISSION         PIC X(001).    00004900
005000         88  :VM9BC50T:-CONDITIONS-EMISSION        VALUE 'Y'.     00005000
005100     30  :VM9BC50T:-DA-DEMANDE                     PIC X(008).    00005100
005200     30  FILLER REDEFINES :VM9BC50T:-DA-DEMANDE.                  00005200
005300         32  :VM9BC50T:-DA-DEMANDE-YY.                            00005300
005400             34  :VM9BC50T:-DA-DEMANDE-Y1          PIC 9(2).      00005400
005500             34  :VM9BC50T:-DA-DEMANDE-Y2          PIC 9(2).      00005500
005600         32  :VM9BC50T:-DA-DEMANDE-M               PIC 9(2).      00005600
005700         32  :VM9BC50T:-DA-DEMANDE-D               PIC 9(2).      00005700
      * EMAED 20100908>>                                                00005701
005100     30  :VM9BC50T:-NR-PRODUCT                     PIC X(004).    00005710
005100     30  :VM9BC50T:-NS-COND-EMISSION2              PIC S9(4)      00005720
                                                         USAGE COMP.    00005730
           30  :VM9BC50T:-FILLER                         PIC X(094).    00005740
      * EMAED 20100908<<                                                00005750
005800*    END-COPY VM9BC50I.                                           00005800
