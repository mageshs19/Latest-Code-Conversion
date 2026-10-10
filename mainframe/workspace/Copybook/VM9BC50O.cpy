000100*    COPY-ID.           VM9BC50O.                                 00000100
000200*    DESCRIPTION.       RESULTATS DE L'APPEL DU BUSINESS SERVICE. 00000200
000300*    USAGE.             COPY VM9BC50O                             00000300
000400*                         REPLACING ==:VM9BC50T:== BY ==WS==      00000400
000500*    AUTHOR.            J. DEFEYTER.                              00000500
000600*    CODE-READER.                                                 00000600
000700*    CHANGED BY.        JEROEN "JEROD" DE SCHUTTER (DOLMEN)       00000700
000800*    DATE-WRITTEN.      23/04/2002.                               00000800
000900*    DATE-LAST-UPDATE   04/09/2002.                               00000900
001000*    DATE-LAST-UPDATE   11/12/2002 (VHEML).                       00001000
001100*                                                                 00001100
001200*    RECORD LENGTH.     2610                                      00001200
001300******************************************************************00001300
001610*  ATTENTION : LE -ENSURED-OUTPUT EST HARCODE DANS VM9NK27I ET 27O00001610
001620*  =========      ==> MODIFIER EGALEMENT LE VM9NK27I ET VM9NK27O  00001620
001630*                 ==> LA LONGUEUR DU -ENSURED-OUTPUT              00001630
001631*                 ==> DOIT RESTER EGALE A 2180                    00001631
001640******************************************************************00001640
001700     05  :VM9BC50T:-VM9BC50T-OUTPUT.                              00001700
001800     10  :VM9BC50T:-ENSURED-OUTPUT.                               00001800
001900         15  :VM9BC50T:-ENSURED-COMMON-OUTPUT.                    00001900
002000             20  :VM9BC50T:-CO-RETURN.                            00002000
002100                 25  :VM9BC50T:-CO-RETURN-MAJOR     PIC X(0001).  00002100
002200                 25  :VM9BC50T:-CO-RETURN-MINOR     PIC X(0003).  00002200
002300             20  :VM9BC50T:-NB-ACTLEN               PIC 9(0008).  00002300
002400                 88  :VM9BC50T:-NORMAL-ACTLEN       VALUE  2610.  00002400
002500                 88  :VM9BC50T:-ABNORMAL-ACTLEN     VALUE  2610.  00002500
002600        15  :VM9BC50T:-ENSURED-VARIABLE-OUTPUT.                   00002600
002700*                                                                 00002700
002800*       P R O D U K T I N F O  ( BCSECUTB)                        00002800
002900*                                                                 00002900
003000*       NR PRODUCT                                                00003000
003100     24 :VM9BC50T:-NR-ID-SECU            PIC X(4).                00003100
003200*       KREATIEDATUM   YYMD                                       00003200
003300     24 :VM9BC50T:-DA-CRSU-SECU.                                  00003300
003400        26 :VM9BC50T:-DA-CRSU-SECU-YY.                            00003400
003500           28 :VM9BC50T:-DA-CRSU-SECU-Y1 PIC 9(2).                00003500
003600           28 :VM9BC50T:-DA-CRSU-SECU-Y2 PIC 9(2).                00003600
003700        26 :VM9BC50T:-DA-CRSU-SECU-M     PIC 9(2).                00003700
003800        26 :VM9BC50T:-DA-CRSU-SECU-D     PIC 9(2).                00003800
003900*       DATUM EXPORT   YYMD                                       00003900
004000     24 :VM9BC50T:-DA-CRDI-SECU.                                  00004000
004100        26 :VM9BC50T:-DA-CRDI-SECU-YY.                            00004100
004200           28 :VM9BC50T:-DA-CRDI-SECU-Y1 PIC 9(2).                00004200
004300           28 :VM9BC50T:-DA-CRDI-SECU-Y2 PIC 9(2).                00004300
004400        26 :VM9BC50T:-DA-CRDI-SECU-M     PIC 9(2).                00004400
004500        26 :VM9BC50T:-DA-CRDI-SECU-D     PIC 9(2).                00004500
004600*       MUNTKODE                                                  00004600
004700     24 :VM9BC50T:-CO-CURR-SECU          PIC X(3).                00004700
004800*       UITGIFTEFREQUENTIE                                        00004800
004900     24 :VM9BC50T:-NB-ISSUE-SECU         PIC 9(2).                00004900
005000*       WIJZE VAN SPREIDING                                       00005000
005100     24 :VM9BC50T:-CO-DISTR-SECU         PIC X(1).                00005100
005200*       LOOPTIJD                                                  00005200
005300     24 :VM9BC50T:-DU-TERM-SECU          PIC 9(3).                00005300
005400*       KORTE BESCHRIJVING NL                                     00005400
005500     24 :VM9BC50T:-NM-DESDS-SECU         PIC X(40).               00005500
005600*       LANGE BESCHRIJVING NL                                     00005600
005700     24 :VM9BC50T:-NM-DESDL-SECU         PIC X(70).               00005700
005800*       KORTE BESCHRIJVING FR                                     00005800
005900     24 :VM9BC50T:-NM-DESFS-SECU         PIC X(40).               00005900
006000*       LANGE BESCHRIJVING FR                                     00006000
006100     24 :VM9BC50T:-NM-DESFL-SECU         PIC X(70).               00006100
006200*       KORTE BESCHRIJVING D                                      00006200
006300     24 :VM9BC50T:-NM-DESGS-SECU         PIC X(40).               00006300
006400*       LANGE BESCHRIJVING D                                      00006400
006500     24 :VM9BC50T:-NM-DESGL-SECU         PIC X(70).               00006500
006510*       KORTE BESCHRIJVING E                                      00006510
006520     24 :VM9BC50T:-NM-DESES-SECU         PIC X(40).               00006520
006530*       LANGE BESCHRIJVING E                                      00006530
006540     24 :VM9BC50T:-NM-DESEL-SECU         PIC X(70).               00006540
006600*       LAATSTE COUPON MANTEL                                     00006600
006700     24 :VM9BC50T:-CO-LAST-COUP          PIC X(01).               00006700
006800*       AFTEKENING/FYSISCH                                        00006800
006900     24 :VM9BC50T:-CO-PHYS-COUP          PIC X(01).               00006900
007000*       PERIODICITEIT VAN DE EERSTE COUPON                        00007000
007100     24 :VM9BC50T:-NB-PERI1-COUP         PIC 9(03).               00007100
007200*       ALGEMENE PERIODICITEIT                                    00007200
007300     24 :VM9BC50T:-NB-PERIA-COUP         PIC 9(03).               00007300
007400*       AANTAL GROEPEN VAN COUPONS                                00007400
007500     24 :VM9BC50T:-NB-GROUP-COUP         PIC 9(02).               00007500
007600*       AANTAL COUPONS                                            00007600
007700     24 :VM9BC50T:-NB-COUP               PIC 9(03).               00007700
007800*       TYPE VAN KAPITALISATIE                                    00007800
007900     24 :VM9BC50T:-CO-TYPE-CAPT          PIC X(1).                00007900
008000*       PERIODE VAN KAPITALISATIE                                 00008000
008100     24 :VM9BC50T:-NB-PERIN-CAPT         PIC 9(3).                00008100
008200*       AARD VAN DE RENTEVOETEN (0=VAST,1=WIJZIGBAAR,2=VARIABEL)  00008200
008300     24 :VM9BC50T:-CO-RFIX-SECU          PIC 9.                   00008300
008400*       CODE EMETTEUR                                             00008400
008500     24 :VM9BC50T:-CO-ISSUE-SECU         PIC X(1).                00008500
008600*       TYPE PRODUCT                                              00008600
008700     24 :VM9BC50T:-CO-TYPE-SECU          PIC X(1).                00008700
008800*       EENHEID VAN UITGIFTEFREQUENTIE                            00008800
008900     24 :VM9BC50T:-CO-TUFIS-SECU         PIC X(1).                00008900
009000*                                                                 00009000
009100*     T U S S E N T I J D S E    V E R V A L D A G E N (BCINEXTB) 00009100
009200*                                                                 00009200
009300*       SWITCH OF ER TTVVD ZIJN                                   00009300
009400     24 :VM9BC50T:-CODE-TTVVD            PIC X(1).                00009400
009500     24 :VM9BC50T:-INEX-TAB.                                      00009500
009600*       AANTAL HALVE MAANDEN DIE VERLOPEN TUSSEN DE INGENOTTRE-   00009600
009700*       DINGSDATUM EN DE BEDOELDE TUSSENTIJDSE VERVALDAG          00009700
009800        26 :VM9BC50T:-NB-TIUT-INEX       PIC 9(3) OCCURS 14.      00009800
009900*                                                                 00009900
010000*     C A L L S    (BCCALLTB)                                     00010000
010100*                                                                 00010100
010200*       SWITCH OF ER CALLS ZIJN                                   00010200
010300     24 :VM9BC50T:-CODE-CALL             PIC X(1).                00010300
010400     24 :VM9BC50T:-CALL-TAB.                                      00010400
010500*       AANTAL HALVE MAANDEN DIE VERLOPEN TUSSEN DE INGENOTTRE-   00010500
010600*       DINGSDATUM EN DE BEDOELDE CALL                            00010600
010700        26 :VM9BC50T:-NB-TIUT-CALL       PIC 9(3) OCCURS 14.      00010700
010800*                                                                 00010800
010900*     V E R K O O P S V O O R W A A R D E N (BCSACOTB)            00010900
011000*                                                                 00011000
011100*       VOLGNUMMER KREATIE VERKOOPSVOORWAARDEN                    00011100
011200     24 :VM9BC50T:-NS-CREAT-SACO         PIC 9(5).                00011200
011300*       KREATIEDATUM VERKOOPSVOORWAARDEN YYMD                     00011300
011400     24 :VM9BC50T:-DA-CREAT-SACO.                                 00011400
011500        26 :VM9BC50T:-DA-CREAT-SACO-YY.                           00011500
011600           28 :VM9BC50T:-DA-CREAT-SACO-Y1 PIC 9(2).               00011600
011700           28 :VM9BC50T:-DA-CREAT-SACO-Y2 PIC 9(2).               00011700
011800        26 :VM9BC50T:-DA-CREAT-SACO-M     PIC 9(2).               00011800
011900        26 :VM9BC50T:-DA-CREAT-SACO-D     PIC 9(2).               00011900
012000*       AKTIVATIEDATUM VERKOOPSVOORWAARDEN YYMD                   00012000
012100     24 :VM9BC50T:-DA-ACTIV-SACO.                                 00012100
012200        26 :VM9BC50T:-DA-ACTIV-SACO-YY.                           00012200
012300           28 :VM9BC50T:-DA-ACTIV-SACO-Y1 PIC 9(2).               00012300
012400           28 :VM9BC50T:-DA-ACTIV-SACO-Y2 PIC 9(2).               00012400
012500        26 :VM9BC50T:-DA-ACTIV-SACO-M     PIC 9(2).               00012500
012600        26 :VM9BC50T:-DA-ACTIV-SACO-D     PIC 9(2).               00012600
012700*       AL OF NIET VASTEGELEGDE COUPURES                          00012700
012800     24 :VM9BC50T:-CO-DENO-SACO           PIC X(1).               00012800
012900*       HOOGST TOEGELATEN COUPURE                                 00012900
013000     24 :VM9BC50T:-AM-SDEN-SACO           PIC 9(13)V9(2).         00013000
013100*       LAAGST TOEGELATEN COUPURE                                 00013100
013200     24 :VM9BC50T:-AM-IDEN-SACO           PIC 9(13)V9(2).         00013200
013300*       HOOGST TOEGELATEN INTEKENING                              00013300
013400     24 :VM9BC50T:-AM-SCNS-SACO           PIC 9(13)V9(2).         00013400
013500*       LAAGST TOEGELATEN INTEKENING                              00013500
013600     24 :VM9BC50T:-AM-ICNS-SACO           PIC 9(13)V9(2).         00013600
013700*       RENTEVOET GESCHENKPREMIE                                  00013700
013800     24 :VM9BC50T:-RA-PPREM-SACO          PIC 9(3)V9(3).          00013800
013900*       MINIMUM BEDRAG GESCHENKPREMIE                             00013900
014000     24 :VM9BC50T:-AM-PSUB-SACO           PIC 9(13)V9(2).         00014000
014100*       AL OF NIET BELASTING OP GESCHENKPREMIE                    00014100
014200     24 :VM9BC50T:-CO-PTAX-SACO           PIC X(1).               00014200
014300*       LANCERINGSDATUM PRODUKT YYMD                              00014300
014400     24 :VM9BC50T:-DA-START-SACO.                                 00014400
014500        26 :VM9BC50T:-DA-START-SACO-YY.                           00014500
014600           28 :VM9BC50T:-DA-START-SACO-Y1 PIC 9(2).               00014600
014700           28 :VM9BC50T:-DA-START-SACO-Y2 PIC 9(2).               00014700
014800        26 :VM9BC50T:-DA-START-SACO-M     PIC 9(2).               00014800
014900        26 :VM9BC50T:-DA-START-SACO-D     PIC 9(2).               00014900
015000*       DATUM TERUGTREKKING VAN DE MARKT YYMD                     00015000
015100     24 :VM9BC50T:-DA-RETR-SACO.                                  00015100
015200        26 :VM9BC50T:-DA-RETR-SACO-YY.                            00015200
015300           28 :VM9BC50T:-DA-RETR-SACO-Y1  PIC 9(2).               00015300
015400           28 :VM9BC50T:-DA-RETR-SACO-Y2  PIC 9(2).               00015400
015500        26 :VM9BC50T:-DA-RETR-SACO-M      PIC 9(2).               00015500
015600        26 :VM9BC50T:-DA-RETR-SACO-D      PIC 9(2).               00015600
015700*       HARMONISATIE NA TERUGTREKKING VAN DE MARKT                00015700
015800     24 :VM9BC50T:-CO-HARM-SACO           PIC X(1).               00015800
015900*       TIJDSEENHEID TUSSENTIJDSE INTRESTEN                       00015900
016000     24 :VM9BC50T:-CO-TUII-SACO           PIC X(1).               00016000
016100*       BUDGET DAGELIJKSE TUSSENTIJDSE INTRESTEN                  00016100
016200     24 :VM9BC50T:-CO-BUII-SACO           PIC X(1).               00016200
016300*       MAXIMUM AANTAL HALVE MAANDEN                              00016300
016400     24 :VM9BC50T:-NB-MXFII-SACO          PIC 9(3).               00016400
016500*       ALGEMENE/SPECIFIEKE % VOOR HV TTI'S                       00016500
016600     24 :VM9BC50T:-CO-RUFII-SACO          PIC X(1).               00016600
016700*       % HV TTI'S                                                00016700
016800     24 :VM9BC50T:-RA-FII-SACO            PIC 9(3)V9(3).          00016800
016900*       ALGEMENE/SPECIFIEKE % VOOR DAGELIJKSE TTI'S               00016900
017000     24 :VM9BC50T:-CO-RUDII-SACO          PIC X(1).               00017000
017100*       % DAGELIJKSE TTI'S                                        00017100
017200     24 :VM9BC50T:-RA-DII-SACO            PIC 9(3)V9(3).          00017200
017300*       ALGEMENE/SPECIFIEKE VOOR PERIODE RVW                      00017300
017400     24 :VM9BC50T:-CO-RUCH-SACO           PIC X(1).               00017400
017500*       AANTAL HM VOOR RVW                                        00017500
017600     24 :VM9BC50T:-NB-FBCH-SACO           PIC 9(3).               00017600
017700*       AANTAL HM NA RVW                                          00017700
017800     24 :VM9BC50T:-NB-FACH-SACO           PIC 9(3).               00017800
017900*       ALGEMENE/SPECIFIEKE VOOR DE OBI'S                         00017900
018000     24 :VM9BC50T:-CO-RUBI-SACO           PIC X(1).               00018000
018100*       MAX AANTAL PRIMAIRE HM AAN OBI                            00018100
018200     24 :VM9BC50T:-NB-MXPFB-SACO          PIC 9(3).               00018200
018300*       % VOOR PRIMAIRE HM AAN OBI                                00018300
018400     24 :VM9BC50T:-RA-PFB-SACO            PIC 9(3)V9(3).          00018400
018500*       MAX AANTAL SECUNDAIRE HM AAN OBI                          00018500
018600     24 :VM9BC50T:-NB-MXSFB-SACO          PIC 9(3).               00018600
018700*       % VOOR SECUNDAIRE HM AAN OBI                              00018700
018800     24 :VM9BC50T:-RA-SFB-SACO            PIC 9(3)V9(3).          00018800
018900*       ALGEMEEN/SPECIFIEK VOOR VALUTADATUM                       00018900
019000     24 :VM9BC50T:-CO-RUVD-SACO           PIC X(1).               00019000
019100*       MAX AANTAL HM DAT DE VALUTADATUM KAN VERSCHOVEN WORDEN    00019100
019200     24 :VM9BC50T:-NB-MXFVD-SACO          PIC 9(3).               00019200
019300*       AANTAL QUINZAINES  VOOR DE COUPONBETALING TOEGELATEN      00019300
019400     24 :VM9BC50T:-NB-FBPC-SACO           PIC 9(3).               00019400
019500*       AANTAL QUINZAINES  VOOR DE TTVVD TOEGELATEN               00019500
019600     24 :VM9BC50T:-NB-FBIE-SACO           PIC 9(3).               00019600
019700*       AANTAL QUINZAINES  NA   DE TTVVD TOEGELATEN               00019700
019800     24 :VM9BC50T:-NB-FAIE-SACO           PIC 9(3).               00019800
019900*       AANTAL QUINZAINES  VOOR DE EVVD TOEGELATEN                00019900
020000     24 :VM9BC50T:-NB-FBFE-SACO           PIC 9(3).               00020000
020100*       MASKER VAN HET PRODUKT                                    00020100
020200     24 :VM9BC50T:-NR-IDPM-SACO           PIC 9(4).               00020200
020300*                                                                 00020300
020400*     V A S T G E L E G D E   C O U P U R E S (BCDENOTB)          00020400
020500*                                                                 00020500
020600     24 :VM9BC50T:-DENO-TAB.                                      00020600
020700*       BEDRAG VOORAF VASTGELEGDE COUPURE                         00020700
020800        26 :VM9BC50T:-AM-PCND-DENO       PIC 9(13)V9(2) OCCURS 10.00020800
020900*                                                                 00020900
021000*     U I T G I F T E V O O R W A A R D E N   (BCIRMOTB)          00021000
021100*                                                                 00021100
021200*       VOLGNUMMER VAN DE WIJZIGING UITGIFTEVOORWAARDEN           00021200
021300     24 :VM9BC50T:-NS-SEQ-IRMO           PIC 9(5).                00021300
021400*       FACIALE RENTEVOET                                         00021400
021500     24 :VM9BC50T:-RA-FA-IRMO            PIC 9(3)V9(3).           00021500
021600*       DATUM KONTROLE RENTEVOETWIJZIGING  YYMD                   00021600
021700     24 :VM9BC50T:-DA-CONTR-IRMO.                                 00021700
021800        26 :VM9BC50T:-DA-CONTR-IRMO-YY.                           00021800
021900           28 :VM9BC50T:-DA-CONTR-IRMO-Y1 PIC 9(2).               00021900
022000           28 :VM9BC50T:-DA-CONTR-IRMO-Y2 PIC 9(2).               00022000
022100        26 :VM9BC50T:-DA-CONTR-IRMO-M     PIC 9(2).               00022100
022200        26 :VM9BC50T:-DA-CONTR-IRMO-D     PIC 9(2).               00022200
022300*       KODE ROERENDE VOORHEFFING                                 00022300
022400     24 :VM9BC50T:-CO-PRTI-IRMO           PIC X(1).               00022400
022500*       UITGIFTEPREMIE                                            00022500
022600     24 :VM9BC50T:-RA-PRSH-IRMO           PIC 9(3)V9(3).          00022600
022700*       DATUM INVOEGETREDING RENTEVOETWIJZIGING  YYMD             00022700
022800     24 :VM9BC50T:-DA-UBISS-IRMO.                                 00022800
022900        26 :VM9BC50T:-DA-UBISS-IRMO-YY.                           00022900
023000           28 :VM9BC50T:-DA-UBISS-IRMO-Y1 PIC 9(2).               00023000
023100           28 :VM9BC50T:-DA-UBISS-IRMO-Y2 PIC 9(2).               00023100
023200        26 :VM9BC50T:-DA-UBISS-IRMO-M     PIC 9(2).               00023200
023300        26 :VM9BC50T:-DA-UBISS-IRMO-D     PIC 9(2).               00023300
023400*       KREATIEDATUM RENTEVOETWIJZIGING  YYMD                     00023400
023500     24 :VM9BC50T:-DA-CREAT-IRMO.                                 00023500
023600        26 :VM9BC50T:-DA-CREAT-IRMO-YY.                           00023600
023700           28 :VM9BC50T:-DA-CREAT-IRMO-Y1 PIC 9(2).               00023700
023800           28 :VM9BC50T:-DA-CREAT-IRMO-Y2 PIC 9(2).               00023800
023900        26 :VM9BC50T:-DA-CREAT-IRMO-M     PIC 9(2).               00023900
024000        26 :VM9BC50T:-DA-CREAT-IRMO-D     PIC 9(2).               00024000
024100*       INGENOTTREDINGSDATUM EERSTE WAARDEKODE   YYMD             00024100
024200     24 :VM9BC50T:-DA-FUBSE-IRMO.                                 00024200
024300        26 :VM9BC50T:-DA-FUBSE-IRMO-YY.                           00024300
024400           28 :VM9BC50T:-DA-FUBSE-IRMO-Y1 PIC 9(2).               00024400
024500           28 :VM9BC50T:-DA-FUBSE-IRMO-Y2 PIC 9(2).               00024500
024600        26 :VM9BC50T:-DA-FUBSE-IRMO-M     PIC 9(2).               00024600
024700        26 :VM9BC50T:-DA-FUBSE-IRMO-D     PIC 9(2).               00024700
024800*                                                                 00024800
024900*     K A P I T A L I S A T I E R E N T E V O E T (BCCARATB)      00024900
025000*                                                                 00025000
025100     24 :VM9BC50T:-CARA-TAB.                                      00025100
025200*       KAPITALISATIERENTEVOET PER PERIODE                        00025200
025300        26 :VM9BC50T:-RA-CAPT-CARA        PIC 9(3)V9(3) OCCURS 15.00025300
025400*                                                                 00025400
025500*     F A C I A L E   R E N T E V O E T (BCFARATB)                00025500
025600*                                                                 00025600
025700     24 :VM9BC50T:-FARA-TAB.                                      00025700
025800*       FACIALE RENTEVOET PER PERIODE                             00025800
025900        26 :VM9BC50T:-RA-FAC-FARA         PIC 9(3)V9(3) OCCURS 15.00025900
026000*                                                                 00026000
026100*     R A T I O   P E R   V E R V A L D A G (BCPREXTB)            00026100
026200*                                                                 00026200
026300     24 :VM9BC50T:-PREX-TAB.                                      00026300
026400*       RATIO PER VERVALDAG                                       00026400
026500        26 :VM9BC50T:-RA-PROP-PREX PIC 9(2)V9(8) OCCURS 15.       00026500
026600*                                                                 00026600
026700*     R A T I O   P E R   E N K E L V O U D I G E  C O U P O N    00026700
026800*     (BCPRCPTB)                                                  00026800
026900     24 :VM9BC50T:-PRCP-TAB.                                      00026900
027000*       RATIO PER ENKELVOUDIGE COUPON                             00027000
027100        26 :VM9BC50T:-RA-PROP-PRCP PIC 9(2)V9(8) OCCURS 15.       00027100
027200*                                                                 00027200
027300*     R A T I O   P E R   B L O K K E N   V A N  C O U P O N S    00027300
027400*     (BCPRBLTB)                                                  00027400
027500     24 :VM9BC50T:-PRBL-TAB.                                      00027500
027600*       RATIO PER BLOKKEN VAN COUPONS                             00027600
027700        26 :VM9BC50T:-RA-PROP-PRBL PIC 9(2)V9(8) OCCURS 15.       00027700
027800*                                                                 00027800
027900*     T E R U G B E T A L I N G S P R E M I E (BCREPRTB)          00027900
028000*                                                                 00028000
028100     24 :VM9BC50T:-REPR-TAB.                                      00028100
028200*       TERUGBETALINGSPREMIE                                      00028200
028300        26 :VM9BC50T:-RA-PREM-REPR PIC 9(3)V9(3) OCCURS 15.       00028300
028400*                                                                 00028400
028500*     C A L L P R E M I E (BCCAPRTB)                              00028500
028600*                                                                 00028600
028700     24 :VM9BC50T:-CAPR-TAB.                                      00028700
028800*       CALLPREMIE                                                00028800
028900        26 :VM9BC50T:-RA-PREM-CAPR PIC 9(3)V9(3) OCCURS 15.       00028900
029000*                                                                 00029000
029100*     W A A R D E K O D E (BCISSUTB)                              00029100
029200*                                                                 00029200
029300*       WAARDECODE                                                00029300
029400     24 :VM9BC50T:-NR-ID-ISSU             PIC X(9).               00029400
029500*       INGENOTTREDINGSDATUM WAARDEKODE  YYMD                     00029500
029600     24 :VM9BC50T:-DA-UBSEC-ISSU.                                 00029600
029700        26 :VM9BC50T:-DA-UBSEC-ISSU-YY.                           00029700
029800           28 :VM9BC50T:-DA-UBSEC-ISSU-Y1 PIC 9(2).               00029800
029900           28 :VM9BC50T:-DA-UBSEC-ISSU-Y2 PIC 9(2).               00029900
030000        26 :VM9BC50T:-DA-UBSEC-ISSU-M PIC 9(2).                   00030000
030100        26 :VM9BC50T:-DA-UBSEC-ISSU-D PIC 9(2).                   00030100
030200*       KREATIEDATUM WAARDEKODE  YYMD                             00030200
030300     24 :VM9BC50T:-DA-CREAT-ISSU.                                 00030300
030400        26 :VM9BC50T:-DA-CREAT-ISSU-YY.                           00030400
030500           28 :VM9BC50T:-DA-CREAT-ISSU-Y1 PIC 9(2).               00030500
030600           28 :VM9BC50T:-DA-CREAT-ISSU-Y2 PIC 9(2).               00030600
030700        26 :VM9BC50T:-DA-CREAT-ISSU-M PIC 9(2).                   00030700
030800        26 :VM9BC50T:-DA-CREAT-ISSU-D PIC 9(2).                   00030800
030900*       EINDVERVALDAG  YYMD                                       00030900
031000     24 :VM9BC50T:-DA-TERM-SECU.                                  00031000
031100        26 :VM9BC50T:-DA-TERM-SECU-YY.                            00031100
031200           28 :VM9BC50T:-DA-TERM-SECU-Y1 PIC 9(2).                00031200
031300           28 :VM9BC50T:-DA-TERM-SECU-Y2 PIC 9(2).                00031300
031400        26 :VM9BC50T:-DA-TERM-SECU-M PIC 9(2).                    00031400
031500        26 :VM9BC50T:-DA-TERM-SECU-D PIC 9(2).                    00031500
031600     24 :VM9BC50T:-INEX-TAB2.                                     00031600
031700*       TUSSENTIJDSE VERVALDAGEN                                  00031700
031800        26 :VM9BC50T:-DA-TIUT-INEX             OCCURS 14.         00031800
031900        28 :VM9BC50T:-DA-TIUT-INEX-YY.                            00031900
032000           30 :VM9BC50T:-DA-TIUT-INEX-Y1 PIC 9(2).                00032000
032100           30 :VM9BC50T:-DA-TIUT-INEX-Y2 PIC 9(2).                00032100
032200        28 :VM9BC50T:-DA-TIUT-INEX-M     PIC 9(2).                00032200
032300        28 :VM9BC50T:-DA-TIUT-INEX-D     PIC 9(2).                00032300
032400     24 :VM9BC50T:-CALL-TAB2.                                     00032400
032500*       VERVALDAGEN VAN DE CALLS                                  00032500
032600        26 :VM9BC50T:-DA-TIUT-CALL             OCCURS 14.         00032600
032700        28 :VM9BC50T:-DA-TIUT-CALL-YY.                            00032700
032800           30 :VM9BC50T:-DA-TIUT-CALL-Y1 PIC 9(2).                00032800
032900           30 :VM9BC50T:-DA-TIUT-CALL-Y2 PIC 9(2).                00032900
033000        28 :VM9BC50T:-DA-TIUT-CALL-M     PIC 9(2).                00033000
033100        28 :VM9BC50T:-DA-TIUT-CALL-D     PIC 9(2).                00033100
033200*       WIJZIGING RENTEVOETEN VAN DE WAARDEKODE                   00033200
033300     24 :VM9BC50T:-DA-MORA-ISSU          PIC 9(8).                00033300
033400*       INTERN NUMMER UITGIFTE                                    00033400
033500     24 :VM9BC50T:-NM-ID-ISSU            PIC X(11).               00033500
033600*                                                                 00033600
033700*                                                                 00033700
033800*     P U T P R E M I E (BCINPRTB)                                00033800
033900*                                                                 00033900
034000     24 :VM9BC50T:-INPR-TAB.                                      00034000
034100*       PUTPREMIE                                                 00034100
034200        26 :VM9BC50T:-RA-PREM-INPR       PIC 9(3)V9(3) OCCURS 15. 00034200
034300*                                                                 00034300
034400*                                                                 00034400
034500*     M A N T E L   +   C O U P O N S                             00034500
034600*                                                                 00034600
034700*       SW TERUGBETALING MANTEL                                   00034700
034800     24 :VM9BC50T:-SW-REMB-MANT          PIC X(01).               00034800
034900*       VERVALDAG MANTEL                                          00034900
035000     24 :VM9BC50T:-DA-TERM-MANT.                                  00035000
035100        26 :VM9BC50T:-DA-TERM-MANT-YY.                            00035100
035200           28 :VM9BC50T:-DA-TERM-MANT-Y1 PIC 9(02).               00035200
035300           28 :VM9BC50T:-DA-TERM-MANT-Y2 PIC 9(02).               00035300
035400        26 :VM9BC50T:-DA-TERM-MANT-M     PIC 9(02).               00035400
035500        26 :VM9BC50T:-DA-TERM-MANT-D     PIC 9(02).               00035500
035600*       RANG COUPON PAYABLE EN DATE OPERATION                     00035600
035700     24 :VM9BC50T:-NS-RANG-COUP          PIC 9(03).               00035700
035800*       RANG COUPON FORME NORMALE EN DATE OPERATION               00035800
035900     24 :VM9BC50T:-NS-NORM-COUP          PIC 9(03).               00035900
036000*       RANG COUPON FORME NORMALE EN DATE JOUR                    00036000
036100     24 :VM9BC50T:-NS-NORMJ-COUP         PIC 9(03).               00036100
036200*                                                                 00036200
036300*       FILLER                                                    00036300
036301*       SWITCH BC SUBORDONNE Y/N : POSITIONNE EN FONCTION         00036301
036302*       DU N° DE MASQUE                                           00036302
036310     24 :VM9BC50T:-SW-SUBORD             PIC X(01).               00036310
036320     24 :VM9BC50T:-CO-POSIT-040IRMO      PIC X(01).               00036320
036330     24 :VM9BC50T:-CO-BONIF-040IRMO      PIC X(01).               00036330
036400*    24 FILLER                           PIC X(21).               00036400
036401*       SWITCH BC CITIZENSLENDINGSTATUS                           00036401
036402     24 :VM9BC50T:-SW-VOLKSL             PIC X(01).               00036402
036403     24 FILLER                           PIC X(20).               00036403
036404*                                                                 00036404
036410     10 FILLER                           PIC X(139).              00036410
036500*                                                                 00036500
036600     10  :VM9BC50T:-OPTIONAL-OUTPUT.                              00036600
036700         15  :VM9BC50T:-OPTIONAL-COMMON-OUTPUT.                   00036700
036800             20  :VM9BC50T:-ERROR-INFORMATION.                    00036800
036900                 25  :VM9BC50T:-ERROR-MESSAGE.                    00036900
037000                     30  :VM9BC50T:-CO-ERR-GRAVITY PIC X(0001).   00037000
037100                     30  :VM9BC50T:-CO-ERR-SUBS    PIC X(0001).   00037100
037200                     30  :VM9BC50T:-CO-ERR-CODE    PIC X(0006).   00037200
037300                 25  :VM9BC50T:-NM-ERR-MODULE      PIC X(0008).   00037300
037400                 25  :VM9BC50T:-NB-ERR-POSN        PIC 9(0006).   00037400
037500                 25  :VM9BC50T:-TE-ERR-MESSAGE     PIC X(0150).   00037500
037600         15  FILLER                                PIC X(0028).   00037600
037700     10  FILLER                                    PIC X(0079).   00037700
037800*    END-COPY VM9BC50O.                                           00037800
