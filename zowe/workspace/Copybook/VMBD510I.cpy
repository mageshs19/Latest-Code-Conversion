000100*+++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++00000100
000200*                  -- VMBD510I --                                 00000200
000300*  DESCRIPTION : FICHIER VENANT DE LA CHAINE VMBD - CONTROLE      00000300
000400*                ET TRAITEMENT DES OPERATIONS BCI.                00000400
000500*                IL EST CREE DANS LES PROGRAMMES QUI FONT DES     00000500
000600*                CONTROLES SUR LES OPERATIONS.                    00000600
000700*                LE FICHIER EST COMPLÉTÉ DANS LA CHAINE VMBV PAR  00000700
000800*                LES PROGRAMMES QUI PRÉPARENT LA COMPTABILITE.    00000800
000900*                                                                 00000900
001000*                LE RECORD EST COPIE DU RECORD VMBD205I           00001000
001100*                      1 - 1200   REPRIS DE VMBD205I              00001100
001200*                   1201 - 1500   ZONES POUR COMPTA               00001200
001300*                                                                 00001300
001400*         --->   WIJZIGINGEN IN POSITIES 1 - 1200 OOK <---        00001400
001500*         --->   AANBRENGEN IN VMBD205I ||            <---        00001500
001600*                                                                 00001600
001700*  LRECL       : 1500                                             00001700
001800*  MODIFICATIONS                                                  00001800
001900*    09/96       J-M BOOGAERTS                                    00001900
002000*                (REPRIS DU VMBD510V ET REVU POUR L'EURO)         00002000
002100*    02/98       KOEN DE SCHEPPER                                 00002100
002200*                CODE TEST-REEEL TOEGEVOEGD CO-TST-OPER           00002200
002300*    10/2001     JEROEN DE SCHUTTER : TOEVOEGING                  00002300
002400*                BEDRAG TARIEF FYSISCHE LEVERING AAN KLANT        00002400
002500*    06/2003     H.DE VELDER                                      00002500
002600*                AANGEVULD OM OOK VMBVBCIX, VMBASLKX, VMBAMINX    00002600
002700*                EN VMBAPAYX TE VERVANGEN                         00002700
002800*    09/2003     THEUJ                                            00002800
002900*                TOEVOEGING STATUS UITBETALING (CO-STREMB)        00002900
003000*                '1' = UITBETALING OP EVVD                        00003000
003100*                '2' = UITBETALING OP TVVD                        00003100
003200*    10/2003     VHEML (ES164 VM1BD610)                           00003200
003300*                TOEVOEGING CI OMLOOP EFFECT (NR-CI-OM-FORM-AS)   00003300
003400*    11/2004     SECUA                                            00003400
003500*                TOEVOEGING ZONES EFI/RFE                         00003500
003600*    02/2005     VHEML                                            00003600
003700*                VERWIJDEREN REDEFINE CO-SIT-PAY (TERMA)          00003700
003800*                PIC 99 MOEST PIC XX ZIJN VOOR CO-SIT-OPER        00003800
003900*                                                                 00003900
003960*    07/2007  -  J-M BOOGAERTS                                    00003960
003970*                     AJOUT MT BASE RFE                           00003970
      *    22/07/10 :  IELEE - P31 : PRJ 5680  POSITIEBEHEER            00003971
      *                ADD NR-REFINT - NS-REFPO                         00003972
      *    24/04/12 :  TERMA 24/04/12 : P39 : PRJ 131851 DI RUPO        00003973
      *                 ADD CO-TDR EN RA-TDR                            00003974
      *    09/08/12 :  IELEE 09/08/12 : P39 : PRJ 131851 DI RUPO        00003975
      *                 ADD DA-COMPTA-ORIG-OPER                         00003976
      *    25/08/14 :  IELEE 25/08/14 : P47 : PRJ 159770 FATCA          00003977
      *                 ADD CO-FATCA, CO-POSTPON, TS-ENDVAL             00003978
      *                                                                 00003979
003980*                                                                 00003980
003990*                                                                 00003990
004000****************************************************************  00004000
004100*+++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++00004100
004200*----- POS 001 - 1500 -----                                       00004200
004300 01  VMBD510I.                                                    00004300
004400*                                                                 00004400
004500*+++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++00004500
004600*-----           I N F O   O P E R A T I O N                 -----00004600
004700*                ---------------------------                      00004700
004800*----- 001 - 200 -----                                            00004800
004900    10 INFO-OPERATION.                                            00004900
005000*                                                                 00005000
005100*----- 001 - 006 -----  CI OPERATION                              00005100
005200       15 NR-CIO-FORM-AS.                                         00005200
005300          20 NR-CIO-FORM-AS-R           PIC 9(6).                 00005300
005400*                                                                 00005400
005500       15 NR-CIO-MESS-RE          REDEFINES NR-CIO-FORM-AS.       00005500
005600          20 NR-CIO-MESS-RE-R           PIC 9(6).                 00005600
005700*                                                                 00005700
005800       15 NR-CIO-GDIFC-R          REDEFINES NR-CIO-FORM-AS.       00005800
005900          20 NR-CIO-GDIFC               PIC 9(6).                 00005900
006000*                                                                 00006000
006100       15 NR-CIO-OORD-X           REDEFINES NR-CIO-FORM-AS.       00006100
006200          20 NR-CIO-OORD                PIC 9(6).                 00006200
006300*                                                                 00006300
006400       15 NR-CIO-POKB-X           REDEFINES NR-CIO-FORM-AS.       00006400
006500          20 NR-CIO-POKB                PIC 9(6).                 00006500
006600*                                                                 00006600
006700       15 NR-CIO-OPER-X           REDEFINES NR-CIO-FORM-AS.       00006700
006800          20 NR-CIO-OPER                PIC 9(6).                 00006800
006900*                                                                 00006900
007000       15 NR-CIO-COUP-R           REDEFINES NR-CIO-FORM-AS.       00007000
007100          20 NR-CIO-COUP                PIC 9(6).                 00007100
007200*                                                                 00007200
007300       15 NR-CIO-PAY-R            REDEFINES NR-CIO-FORM-AS.       00007300
007400          20 NR-CIO-PAY                 PIC 9(6).                 00007400
007500*                                                                 00007500
007600*----- 007 - 012 -----  DI                                        00007600
007700       15 NR-ID-FORM-AS                 PIC 9(6).                 00007700
007800       15 NR-ID-FORM-AS-R         REDEFINES NR-ID-FORM-AS.        00007800
007900          20 NR-ID-FORM-AS-R1           PIC 9(5).                 00007900
008000          20 NR-ID-FORM-AS-R2           PIC 9.                    00008000
008100*                                                                 00008100
008200       15 NR-ID-MESS-RE           REDEFINES NR-ID-FORM-AS.        00008200
008300          20 NR-ID-MESS-RE-R            PIC 9(6).                 00008300
008400*                                                                 00008400
008500       15 NR-ID-GDIFC-R           REDEFINES NR-ID-FORM-AS.        00008500
008600          20 NR-ID-GDIFC                PIC 9(6).                 00008600
008700*                                                                 00008700
008800       15 NR-DI-OORD-X            REDEFINES NR-ID-FORM-AS.        00008800
008900          20 NR-DI-OORD                 PIC 9(6).                 00008900
009000*                                                                 00009000
009100       15 NR-DI-POKB-X            REDEFINES NR-ID-FORM-AS.        00009100
009200          20 NR-DI-POKB                 PIC 9(6).                 00009200
009300*                                                                 00009300
009400       15 NR-ID-OPER-X            REDEFINES NR-ID-FORM-AS.        00009400
009500          20 NR-ID-OPER                 PIC 9(6).                 00009500
009600*                                                                 00009600
009700       15 NR-ID-COUP-X            REDEFINES NR-ID-FORM-AS.        00009700
009800          20 NR-ID-COUP                 PIC 9(6).                 00009800
009900*                                                                 00009900
010000       15 NR-ID-PAY-X             REDEFINES NR-ID-FORM-AS.        00010000
010100          20 NR-ID-PAY                  PIC 9(6).                 00010100
010200*                                                                 00010200
010300*----- 013 - 020 -----  DATE CREATION DU DOCUMENT                 00010300
010400       15 DA-CREA-FORM-AS.                                        00010400
010500          20 DA-CR-FORM-AS-Y.                                     00010500
010600             25 DA-CR-FORM-AS-Y1        PIC XX.                   00010600
010700             25 DA-CR-FORM-AS-Y2        PIC XX.                   00010700
010800          20 DA-CR-FORM-AS-M            PIC XX.                   00010800
010900          20 DA-CR-FORM-AS-D            PIC XX.                   00010900
011000*                                                                 00011000
011100       15 FILLER                  REDEFINES DA-CREA-FORM-AS.      00011100
011200          20 DA-CREA-FORM-AS-R          PIC 9(8).                 00011200
011300*                                                                 00011300
011400       15 DA-CR-MESS-RE           REDEFINES DA-CREA-FORM-AS.      00011400
011500          20 DA-CR-MESS-RE-Y.                                     00011500
011600             25 DA-CR-MESS-RE-Y1        PIC XX.                   00011600
011700             25 DA-CR-MESS-RE-Y2        PIC XX.                   00011700
011800          20 DA-CR-MESS-RE-M            PIC XX.                   00011800
011900          20 DA-CR-MESS-RE-D            PIC XX.                   00011900
012000*                                                                 00012000
012100       15 FILLER                  REDEFINES DA-CREA-FORM-AS.      00012100
012200          20 DA-CR-MESS-RE-R            PIC 9(8).                 00012200
012300*                                                                 00012300
012400       15 DA-CR-GDIFC-R           REDEFINES DA-CREA-FORM-AS.      00012400
012500          20 DA-CR-GDIFC                PIC 9(8).                 00012500
012600*                                                                 00012600
012700       15 DA-CR-OORD-X            REDEFINES DA-CREA-FORM-AS.      00012700
012800          20 DA-CR-OORD                 PIC 9(8).                 00012800
012900*                                                                 00012900
013000       15 DA-CR-POKB-X            REDEFINES DA-CREA-FORM-AS.      00013000
013100          20 DA-CR-POKB                 PIC 9(8).                 00013100
013200*                                                                 00013200
013300       15 DA-CR-OPER-X            REDEFINES DA-CREA-FORM-AS.      00013300
013400          20 DA-CR-OPER                 PIC 9(8).                 00013400
013500*                                                                 00013500
013600       15 DA-CR-COUP-X            REDEFINES DA-CREA-FORM-AS.      00013600
013700          20 DA-CR-COUP                 PIC 9(8).                 00013700
013800*                                                                 00013800
013900       15 DA-CR-PAY-X             REDEFINES DA-CREA-FORM-AS.      00013900
014000          20 DA-CR-PAY                  PIC 9(8).                 00014000
014100*                                                                 00014100
014200*----- 021 - 024 -----  CODE OPERATION GENERAL / DETAIL           00014200
014300       15 CT-OP-FORM-AS.                                          00014300
014400          20 CT-OPG-FORM-AS             PIC XX.                   00014400
014500          20 CT-OPD-FORM-AS             PIC XX.                   00014500
014600*                                                                 00014600
014700       15 FILLER                  REDEFINES CT-OP-FORM-AS.        00014700
014800          20 CT-OP-FORM-AS-R            PIC 9(4).                 00014800
014900*                                                                 00014900
015000       15 FILLER                  REDEFINES CT-OP-FORM-AS.        00015000
015100          20 CT-OPG-FORM-AS-R           PIC 99.                   00015100
015200          20 CT-OPD-FORM-AS-R           PIC 99.                   00015200
015300*                                                                 00015300
015400       15 CT-OP-MESS-RE           REDEFINES CT-OP-FORM-AS.        00015400
015500          20 CT-OPG-MESS-RE             PIC XX.                   00015500
015600          20 CT-OPD-MESS-RE             PIC XX.                   00015600
015700*                                                                 00015700
015800       15 FILLER                  REDEFINES CT-OP-FORM-AS.        00015800
015900          20 CT-OP-MESS-RE-R            PIC 9(4).                 00015900
016000*                                                                 00016000
016100       15 FILLER                  REDEFINES CT-OP-FORM-AS.        00016100
016200          20 CT-OPG-MESS-RE-R           PIC 99.                   00016200
016300          20 CT-OPD-MESS-RE-R           PIC 99.                   00016300
016400*                                                                 00016400
016500       15 CT-OP-GDIFC             REDEFINES CT-OP-FORM-AS.        00016500
016600          20 CT-OPG-GDIFC               PIC 99.                   00016600
016700          20 CT-OPD-GDIFC               PIC 99.                   00016700
016800*                                                                 00016800
016900       15 CO-OP-OORD              REDEFINES CT-OP-FORM-AS.        00016900
017000          20 CO-OPG-OORD                PIC 99.                   00017000
017100          20 CO-OPD-OORD                PIC 99.                   00017100
017200*                                                                 00017200
017300       15 FILLER                  REDEFINES CT-OP-FORM-AS.        00017300
017400          20 CO-OPG-OORD-X              PIC XX.                   00017400
017500          20 CO-OPD-OORD-X              PIC XX.                   00017500
017600*                                                                 00017600
017700       15 CO-OP-POKB              REDEFINES CT-OP-FORM-AS.        00017700
017800          20 CO-OPG-POKB                PIC 99.                   00017800
017900          20 CO-OPD-POKB                PIC 99.                   00017900
018000*                                                                 00018000
018100       15 FILLER                  REDEFINES CT-OP-FORM-AS.        00018100
018200          20 FILLER                     PIC XX.                   00018200
018300          20 CT-OPD-COUP                PIC XX.                   00018300
018400*                                                                 00018400
018500       15 FILLER                  REDEFINES CT-OP-FORM-AS.        00018500
018600          20 CO-OPG-POKB-X              PIC XX.                   00018600
018700          20 CO-OPD-POKB-X              PIC XX.                   00018700
018800*                                                                 00018800
018900       15 FILLER                  REDEFINES CT-OP-FORM-AS.        00018900
019000          20 CT-OPG-OPER                PIC XX.                   00019000
019100          20 CT-OPD-OPER                PIC XX.                   00019100
019200*                                                                 00019200
019300       15 FILLER                  REDEFINES CT-OP-FORM-AS.        00019300
019400          20 FILLER                     PIC XX.                   00019400
019500          20 CT-OPD-PAY                 PIC XX.                   00019500
019600*                                                                 00019600
019700*----- 025 - 030 -----  CI POSTE DE TRAVAIL                       00019700
019800       15 NR-CIW-FORM-AS.                                         00019800
019900          20 NR-CIW-FORM-AS-R           PIC 9(6).                 00019900
020000*                                                                 00020000
020100       15 FILLER                  REDEFINES NR-CIW-FORM-AS.       00020100
020200          20 FIL-CIW                    PIC X(6).                 00020200
020300*                                                                 00020300
020400       15 FILLER                  REDEFINES NR-CIW-FORM-AS.       00020400
020500          20 NR-CIW-GDIFC               PIC 9(6).                 00020500
020600*                                                                 00020600
020700       15 NR-CIINPTR-OORD-X       REDEFINES NR-CIW-FORM-AS.       00020700
020800          20 NR-CIINPTR-OORD            PIC 9(6).                 00020800
020900*                                                                 00020900
021000       15 NR-CIINPTR-POKB-X       REDEFINES NR-CIW-FORM-AS.       00021000
021100          20 NR-CIINPTR-POKB            PIC 9(6).                 00021100
021200*                                                                 00021200
021300       15 NR-CIW-OPER-X           REDEFINES NR-CIW-FORM-AS.       00021300
021400          20 NR-CIW-OPER                PIC 9(6).                 00021400
021500*                                                                 00021500
021600       15 NR-CIW-COUP-X           REDEFINES NR-CIW-FORM-AS.       00021600
021700          20 NR-CIW-COUP                PIC 9(6).                 00021700
021800*                                                                 00021800
021900       15 NR-CIW-PAY-R            REDEFINES NR-CIW-FORM-AS.       00021900
022000          20 NR-CIW-PAY                 PIC 9(6).                 00022000
022100*                                                                 00022100
022200*----- 031 - 038 -----  N° POSTE DE TRAVAIL                       00022200
022300       15 NR-WKPOST-OORD-X.                                       00022300
022400          20 NR-WKPOST-OORD             PIC 9(8).                 00022400
022500*                                                                 00022500
022600       15 NR-WKPOST-POKB-X        REDEFINES NR-WKPOST-OORD-X.     00022600
022700          20 NR-WKPOST-POKB             PIC 9(8).                 00022700
022800*                                                                 00022800
022900*----- 039 - 054 -----  N° RÉFÉRENCE DE L'ORDRE                   00022900
023000       15 NR-REFORD-OORD                PIC X(16).                00023000
023100*                                                                 00023100
023200       15 FILLER                  REDEFINES NR-REFORD-OORD.       00023200
023300          20 NR-REFORD-POKB             PIC X(16).                00023300
023400*                                                                 00023400
023500*----- 055 - 057 -----  N° LIGNE DE L'ORDRE                       00023500
023600       15 NS-LINE-OORD                  PIC 9(3).                 00023600
023700*                                                                 00023700
023800       15 FILLER                  REDEFINES NS-LINE-OORD.         00023800
023900          20 NS-LINE-POKB               PIC 9(3).                 00023900
024000*                                                                 00024000
024100       15 FILLER                  REDEFINES NS-LINE-OORD.         00024100
024200          20 NS-LINE-GDIFC              PIC 9(3).                 00024200
024300*                                                                 00024300
024400       15 NS-SEGRP-FORM-AS-R      REDEFINES NS-LINE-OORD.         00024400
024500          20 NS-SEGRP-FORM-AS           PIC 9(3).                 00024500
024600*                                                                 00024600
024700       15 NS-SEGRP-OPER-R         REDEFINES NS-LINE-OORD.         00024700
024800          20 NS-SEGRP-OPER              PIC 9(3).                 00024800
024900*                                                                 00024900
025000       15 FILLER                  REDEFINES NS-LINE-OORD.         00025000
025100          20 NS-LINE-COUP               PIC 9(3).                 00025100
025200*                                                                 00025200
025300       15 FILLER                  REDEFINES NS-LINE-OORD.         00025300
025400          20 NS-LINE-PAY                PIC 9(3).                 00025400
025500*                                                                 00025500
025600*----- 058 - 060 -----  NB LIGNE DE L'ORDRE                       00025600
025700       15 NB-LINE-OORD                  PIC 9(3).                 00025700
025800*                                                                 00025800
025900       15 FILLER                  REDEFINES NB-LINE-OORD.         00025900
026000          20 NB-LINE-GDIFC              PIC 9(3).                 00026000
026100*                                                                 00026100
026200       15 NB-GROUP-FORM-AS-R      REDEFINES NB-LINE-OORD.         00026200
026300          20 NB-GROUP-FORM-AS           PIC 9(3).                 00026300
026400*                                                                 00026400
026500       15 FILLER                  REDEFINES NB-LINE-OORD.         00026500
026600          20 NB-GROUP-OPER              PIC 9(3).                 00026600
026700*                                                                 00026700
026800       15 FILLER                  REDEFINES NB-LINE-OORD.         00026800
026900          20 NB-LINE-COUP               PIC 9(3).                 00026900
027000*                                                                 00027000
027100       15 FILLER                  REDEFINES NB-LINE-OORD.         00027100
027200          20 NB-LINE-PAY                PIC 9(3).                 00027200
027300*                                                                 00027300
027400*----- 061 - 062 -----  TYPE OPERATION SECURITIES                 00027400
027500       15 CO-TYPOPER-OORD               PIC X(2).                 00027500
027600*                                                                 00027600
027700*----- 063 - 088 -----  TIMESTAMP CRÉATION ORDRE                  00027700
027800       15 TS-CREA-OORD                  PIC X(26).                00027800
027900*                                                                 00027900
028000*----- 089 - 094 -----  TYPE TRANSACTION                          00028000
028100       15 CO-TTRANSA-OORD               PIC X(6).                 00028100
028200*                                                                 00028200
028300*----- 095 - 107 -----  N° TRANSACTION                            00028300
028400       15 NR-TRANS-OORD                 PIC X(13).                00028400
028500*                                                                 00028500
028600       15 FILLER                  REDEFINES NR-TRANS-OORD.        00028600
028700          20 NR-TRANS-POKB              PIC X(13).                00028700
028800*                                                                 00028800
028900*----- 108 - 110 -----  DEVISE DE L'OPERATION                     00028900
029000       15 SL-CO-DEV-FORM-AS             PIC X(3).                 00029000
029100*                                                                 00029100
029200       15 FILLER                  REDEFINES SL-CO-DEV-FORM-AS.    00029200
029300          20 CO-DEV-OORD                PIC X(3).                 00029300
029400*                                                                 00029400
029500       15 FILLER                  REDEFINES SL-CO-DEV-FORM-AS.    00029500
029600          20 CO-DEV-POKB                PIC X(3).                 00029600
029700*                                                                 00029700
029800       15 FILLER                  REDEFINES SL-CO-DEV-FORM-AS.    00029800
029900          20 CO-DEV-GDIFC               PIC X(3).                 00029900
030000*                                                                 00030000
030100       15 FILLER                  REDEFINES SL-CO-DEV-FORM-AS.    00030100
030200          20 CO-DEV-COUP                PIC X(3).                 00030200
030300*                                                                 00030300
030400       15 FILLER                  REDEFINES SL-CO-DEV-FORM-AS.    00030400
030500          20 CO-CURR-COUP               PIC X(3).                 00030500
030600*                                                                 00030600
030700       15 FILLER                  REDEFINES SL-CO-DEV-FORM-AS.    00030700
030800          20 CO-CURRC-OPER              PIC X(3).                 00030800
030900*                                                                 00030900
031000       15 FILLER                  REDEFINES SL-CO-DEV-FORM-AS.    00031000
031100          20 CO-CURRC-PAY               PIC X(3).                 00031100
031200*                                                                 00031200
031300*----- 111 - 118 -----  DATE VALEUR DE L'OPERATION                00031300
031400       15 DA-VA-FORM-AS.                                          00031400
031500          20 DA-VA-FORM-AS-Y.                                     00031500
031600             25 DA-VA-FORM-AS-Y1        PIC XX.                   00031600
031700             25 DA-VA-FORM-AS-Y2        PIC XX.                   00031700
031800          20 DA-VA-FORM-AS-M            PIC XX.                   00031800
031900          20 DA-VA-FORM-AS-D            PIC XX.                   00031900
032000*                                                                 00032000
032100       15 FILLER                  REDEFINES DA-VA-FORM-AS.        00032100
032200          20 DA-VA-FORM-AS-R            PIC 9(8).                 00032200
032300*                                                                 00032300
032400       15 FILLER                  REDEFINES DA-VA-FORM-AS.        00032400
032500          20 DA-VA-OORD                 PIC 9(8).                 00032500
032600*                                                                 00032600
032700       15 FILLER                  REDEFINES DA-VA-FORM-AS.        00032700
032800          20 DA-VA-OPER                 PIC 9(8).                 00032800
032900*                                                                 00032900
033000       15 FILLER                  REDEFINES DA-VA-FORM-AS.        00033000
033100          20 DA-VA-COUP                 PIC 9(8).                 00033100
033200*                                                                 00033200
033300       15 FILLER                  REDEFINES DA-VA-FORM-AS.        00033300
033400          20 DA-VA-PAY                  PIC 9(8).                 00033400
033500*                                                                 00033500
033600*----- 119       -----  DATE VALEUR MODIFIEE PAR AGENT            00033600
033700       15 CO-VM-FORM-AS.                                          00033700
033800          20 CO-VM-OORD                 PIC X.                    00033800
033900*                                                                 00033900
034000*----- 120 - 127 -----  DATE EXÉCUTION ORDRE                      00034000
034100       15 DA-EXEC-OORD                  PIC 9(8).                 00034100
034200*                                                                 00034200
034300*----- 128 - 129 -----  CANAL DE DISTRIBUTION                     00034300
034400       15 CO-TYPKAN2-OORD               PIC X(2).                 00034400
034500*                                                                 00034500
034600*----- 130 - 137 -----  USERID DE L'ORDRE                         00034600
034700       15 NR-USER-GDIFC                 PIC X(8).                 00034700
034800*                                                                 00034800
034900       15 FILLER                  REDEFINES NR-USER-GDIFC.        00034900
035000          20 NR-USER-OORD               PIC X(8).                 00035000
035100*                                                                 00035100
035200*----- 138 - 145 -----  DATE VISITE MANUELLE                      00035200
035300       15 DA-BEZACTM-OORD               PIC 9(8).                 00035300
035400*                                                                 00035400
035500*----- 146 - 153 -----  USERID VISITE MANUELLE                    00035500
035600       15 NR-BEZUSEM-OORD               PIC X(8).                 00035600
035700*                                                                 00035700
035800*----- 154 - 169 -----  N° DOCUMENT MANUEL                        00035800
035900       15 NR-DOCUMM-OORD                PIC X(16).                00035900
036000*                                                                 00036000
036100*----- 170 - 172 -----  CODE BACK-OFFICE CONSULT-PROFILE          00036100
036200       15 CO-BACKOFF-OORD               PIC X(3).                 00036200
036300*                                                                 00036300
036400*----- 173 - 174 -----  ORDRE INTRODUCTION BANQUE                 00036400
036500       15 CO-BANK-OORD                  PIC X(2).                 00036500
036600*                                                                 00036600
036700       15 FILLER                  REDEFINES CO-BANK-OORD.         00036700
036800          20 CO-BANK-POKB               PIC X(2).                 00036800
036900*                                                                 00036900
037000*----- 175       -----  TYPE DE VENTE                             00037000
037100       15 CT-SL-FORM-AS                 PIC X.                    00037100
037200*                                                                 00037200
037300       15 FILLER                  REDEFINES CT-SL-FORM-AS.        00037300
037400          20 CO-SEL-OORD                PIC X.                    00037400
037500*                                                                 00037500
037600       15 FILLER                  REDEFINES CT-SL-FORM-AS.        00037600
037700          20 CO-TYPE-OPER               PIC X.                    00037700
037800*                                                                 00037800
037900*----- 176 - 179 -----  CHECK DIGIT                               00037900
038000       15 NR-CD-FORM-AS.                                          00038000
038100          20 NR-CD-FORM-AS-R            PIC 9(4).                 00038100
038200*                                                                 00038200
038300       15 NR-CD-OORD-X            REDEFINES NR-CD-FORM-AS.        00038300
038400          20 NR-CD-OORD                 PIC 9(4).                 00038400
038500*                                                                 00038500
038600       15 NR-CD-POKB-X            REDEFINES NR-CD-FORM-AS.        00038600
038700          20 NR-CD-POKB                 PIC 9(4).                 00038700
038800*                                                                 00038800
038900*----- 180       -----  TYPE ORDRE (R/O)                          00038900
039000       15 CT-LINE-TE                    PIC X.                    00039000
039100*                                                                 00039100
039200       15 FILLER                  REDEFINES CT-LINE-TE.           00039200
039300          20 CO-ORDER-OORD              PIC X.                    00039300
039400*                                                                 00039400
039500       15 FILLER                  REDEFINES CT-LINE-TE.           00039500
039600          20 CT-LINE-TE-OPER            PIC X.                    00039600
039700*                                                                 00039700
039800*----- 181 - 186 -----  CI ÉTOILE                                 00039800
039900       15 NR-CISTER-OORD-X.                                       00039900
040000          20 NR-CISTER-OORD             PIC 9(6).                 00040000
040100*                                                                 00040100
040200*----- 187 - 200 -----  RESERVE                                   00040200
040300       15 FILLER                        PIC X(14).                00040300
040400*                                                                 00040400
040500*+++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++00040500
040600*-----               E M M I S S I O N S                     -----00040600
040700*                    -------------------                          00040700
040800*----- 201 - 300 -----                                            00040800
040900    10 INFO-ISSUE.                                                00040900
041000*----- 201 - 204 -----  N° PRODUIT                                00041000
041100       15 SL-NR-PROD-FORM-AS.                                     00041100
041200         20 NR-ID-040SECU               PIC X(4).                 00041200
041300*                                                                 00041300
041400       15 FILLER REDEFINES SL-NR-PROD-FORM-AS.                    00041400
041500         20 NR-PROD-GDIFC               PIC X(4).                 00041500
041600*                                                                 00041600
041700       15 FILLER REDEFINES SL-NR-PROD-FORM-AS.                    00041700
041800         20 SL-NR-PROD-OPER             PIC X(4).                 00041800
041900*                                                                 00041900
042000       15 FILLER REDEFINES SL-NR-PROD-FORM-AS.                    00042000
042100         20 NR-PROD-COUP                PIC X(4).                 00042100
042200*                                                                 00042200
042300       15 FILLER REDEFINES SL-NR-PROD-FORM-AS.                    00042300
042400         20 NR-SLIK-PAY                 PIC X(4).                 00042400
042500*                                                                 00042500
042600*----- 205 - 208 -----  N° SEQ. COND. ÉMISSION                    00042600
042700       15 NS-SEQ-040IRMO                PIC 9(4).                 00042700
042800*                                                                 00042800
042900*----- 209 - 216 -----  DATE ENTREE EN JOUISSANCE                 00042900
043000       15 DA-UB-FORM-AS.                                          00043000
043100          20 DA-UB-FORM-AS-Y.                                     00043100
043200             25 DA-UB-FORM-AS-Y1        PIC XX.                   00043200
043300             25 DA-UB-FORM-AS-Y2        PIC XX.                   00043300
043400          20 DA-UB-FORM-AS-M            PIC XX.                   00043400
043500          20 DA-UB-FORM-AS-D            PIC XX.                   00043500
043600*                                                                 00043600
043700       15 FILLER                  REDEFINES DA-UB-FORM-AS.        00043700
043800          20 DA-UB-FORM-AS-R            PIC 9(8).                 00043800
043900*                                                                 00043900
044000       15 FILLER                  REDEFINES DA-UB-FORM-AS.        00044000
044100          20 DA-UBSEC-040ISSU           PIC 9(8).                 00044100
044200*                                                                 00044200
044300       15 FILLER                  REDEFINES DA-UB-FORM-AS.        00044300
044400          20 DA-UB-OPER                 PIC 9(8).                 00044400
044500*                                                                 00044500
044600       15 FILLER                  REDEFINES DA-UB-FORM-AS.        00044600
044700          20 DA-UB-ST-COUP              PIC 9(8).                 00044700
044800*                                                                 00044800
044900       15 FILLER                  REDEFINES DA-UB-FORM-AS.        00044900
045000          20 DA-UB-ST-PAY               PIC 9(8).                 00045000
045100*                                                                 00045100
045200*----- 217 - 224 -----  DATE ECHEANCE                             00045200
045300       15 DA-UE-FORM-AS.                                          00045300
045400          20 DA-UE-FORM-AS-Y.                                     00045400
045500             25 DA-UE-FORM-AS-Y1        PIC XX.                   00045500
045600             25 DA-UE-FORM-AS-Y2        PIC XX.                   00045600
045700          20 DA-UE-FORM-AS-M            PIC XX.                   00045700
045800          20 DA-UE-FORM-AS-D            PIC XX.                   00045800
045900*                                                                 00045900
046000       15 FILLER                  REDEFINES DA-UE-FORM-AS.        00046000
046100          20 DA-UE-FORM-AS-R            PIC 9(8).                 00046100
046200*                                                                 00046200
046300       15 FILLER                  REDEFINES DA-UE-FORM-AS.        00046300
046400          20 DA-UE-OPER                 PIC 9(8).                 00046400
046500*                                                                 00046500
046600       15 FILLER                  REDEFINES DA-UE-FORM-AS.        00046600
046700          20 DA-UE-ST-COUP              PIC 9(8).                 00046700
046800*                                                                 00046800
046900       15 FILLER                  REDEFINES DA-UE-FORM-AS.        00046900
047000          20 DA-UE-ST-PAY               PIC 9(8).                 00047000
047100*                                                                 00047100
047200*----- 225 - 227 -----  DUREE DE L'EMISSION                       00047200
047300       15 DU-ST-FORM-AS.                                          00047300
047400          20 DU-ST-FORM-AS-R            PIC 9(3).                 00047400
047500*                                                                 00047500
047600       15 FILLER REDEFINES DU-ST-FORM-AS.                         00047600
047700          20 DU-ST-OPER                 PIC 9(3).                 00047700
047800*                                                                 00047800
047900       15 FILLER REDEFINES DU-ST-FORM-AS.                         00047900
048000          20 DU-ST-COUP                 PIC 9(3).                 00048000
048100*                                                                 00048100
048200       15 FILLER REDEFINES DU-ST-FORM-AS.                         00048200
048300          20 DU-ST-PAY                  PIC 9(3).                 00048300
048400*                                                                 00048400
048500*----- 228 - 230 -----  PERIODICITE 1ER CP                        00048500
048600       15 NB-PERI1-FORM-AS              PIC 9(3).                 00048600
048700*                                                                 00048700
048800       15 FILLER                  REDEFINES NB-PERI1-FORM-AS.     00048800
048900          20 NB-PERI1-GDIFC             PIC 9(3).                 00048900
049000*                                                                 00049000
049100       15 FILLER                  REDEFINES NB-PERI1-FORM-AS.     00049100
049200          20 NB-PERI1-COUP              PIC 9(3).                 00049200
049300*                                                                 00049300
049400       15 FILLER                  REDEFINES NB-PERI1-FORM-AS.     00049400
049500          20 NB-PERI1-PAY               PIC 9(3).                 00049500
049600*                                                                 00049600
049700*----- 231 - 233 -----  PERIODICITE AUTRES CP                     00049700
049800       15 NB-PERIA-FORM-AS              PIC 9(3).                 00049800
049900*                                                                 00049900
050000       15 FILLER                  REDEFINES NB-PERIA-FORM-AS.     00050000
050100          20 NB-PERIA-GDIFC             PIC 9(3).                 00050100
050200*                                                                 00050200
050300       15 FILLER                  REDEFINES NB-PERIA-FORM-AS.     00050300
050400          20 CO-TIUTRA-OPER             PIC 9(3).                 00050400
050500*                                                                 00050500
050600       15 FILLER                  REDEFINES NB-PERIA-FORM-AS.     00050600
050700          20 NB-PERIA-COUP              PIC 9(3).                 00050700
050800*                                                                 00050800
050900       15 FILLER                  REDEFINES NB-PERIA-FORM-AS.     00050900
051000          20 NB-PERIA-PAY               PIC 9(3).                 00051000
051100*                                                                 00051100
051200*----- 234       -----  TYPE DE COUPON                            00051200
051300       15 CO-COUP-FORM-AS               PIC X.                    00051300
051400*                                                                 00051400
051500       15 FILLER                  REDEFINES CO-COUP-FORM-AS.      00051500
051600          20 CO-COUP-GDIFC              PIC X.                    00051600
051700*                                                                 00051700
051800       15 FILLER                  REDEFINES CO-COUP-FORM-AS.      00051800
051900          20 CO-COUP-COUP               PIC X.                    00051900
052000*                                                                 00052000
052100       15 FILLER                  REDEFINES CO-COUP-FORM-AS.      00052100
052200          20 CO-COUP-PAY                PIC X.                    00052200
052300*                                                                 00052300
052400*----- 235       -----  TYPE KAPITALISATIE                        00052400
052500       15 SL-CO-TYPE-CAPT               PIC X.                    00052500
052600*                                                                 00052600
052700       15 FILLER                  REDEFINES SL-CO-TYPE-CAPT.      00052700
052800          20 CO-TYPE-CAPT               PIC X.                    00052800
052900*                                                                 00052900
053000       15 FILLER                  REDEFINES SL-CO-TYPE-CAPT.      00053000
053100          20 CO-FPL-PAY                 PIC X.                    00053100
053200*                                                                 00053200
053300*----- 236 - 239 -----  TAUX DE BASE                              00053300
053400       15 RA-BASE-FORM-AS-R.                                      00053400
053500          20 RA-BASE-FORM-AS            PIC S9(3)V9(3) COMP-3.    00053500
053600*                                                                 00053600
053700       15 FILLER                  REDEFINES RA-BASE-FORM-AS-R.    00053700
053800          20 RA-BS-OPER                 PIC S9(3)V9(3) COMP-3.    00053800
053900*                                                                 00053900
054000*----- 240 - 243 -----  TAUX DE CAPITALISATION                    00054000
054100       15 RA-CP-FORM-AS-R.                                        00054100
054200          20 RA-CP-FORM-AS              PIC S9(3)V9(3) COMP-3.    00054200
054300*                                                                 00054300
054400       15 FILLER                  REDEFINES RA-CP-FORM-AS-R.      00054400
054500          20 RA-CP-OPER                 PIC S9(3)V9(3) COMP-3.    00054500
054600*                                                                 00054600
054700*----- 244 - 247 -----  TAUX DU RACHAT                            00054700
054800       15 RA-SUP-GDIFR-X.                                         00054800
054900           20 RA-SUP-GDIFR              PIC S9(3)V9(3) COMP-3.    00054900
055000*                                                                 00055000
055100       15  FILLER                 REDEFINES RA-SUP-GDIFR-X.       00055100
055200           20 RA-SUP-OORD               PIC S9(3)V9(3) COMP-3.    00055200
055300*                                                                 00055300
055400       15  FILLER                 REDEFINES RA-SUP-GDIFR-X.       00055400
055500           20 RA-SUP-GDIFR-OPER         PIC S9(3)V9(3) COMP-3.    00055500
055600*                                                                 00055600
055700*----- 248 - 251 -----  PRIME EMISSION                            00055700
055800       15 RA-PS-FORM-AS-R.                                        00055800
055900          20 RA-PS-FORM-AS              PIC S9(3)V9(3) COMP-3.    00055900
056000*                                                                 00056000
056100       15 FILLER                  REDEFINES RA-PS-FORM-AS-R.      00056100
056200          20 RA-PS-OPER                 PIC S9(3)V9(3) COMP-3.    00056200
056300*                                                                 00056300
056400*----- 252 - 255 -----  PRIME DE REMBOURSEMENT                    00056400
056500       15 RA-PR-FORM-AS-R.                                        00056500
056600          20 RA-PR-FORM-AS              PIC S9(3)V9(3) COMP-3.    00056600
056700*                                                                 00056700
056800*----- 256 - 259 -----  TAUX DU PUT                               00056800
056900       15 SL-RA-PUT-GDIFAR-X.                                     00056900
057000          20 SL-RA-PUT-GDIFAR           PIC S9(3)V9(3) COMP-3.    00057000
057100*                                                                 00057100
057200       15 FILLER                  REDEFINES SL-RA-PUT-GDIFAR-X.   00057200
057300          20 SL-RA-PUT-OPER             PIC S9(3)V9(3) COMP-3.    00057300
057400*                                                                 00057400
057500*----- 260 - 263 -----  TAUX DES INT. INTERCAL. / QZ              00057500
057600       15 SL-RA-QZTTI-FORM-AS-X.                                  00057600
057700          20 SL-RA-QZTTI-FORM-AS        PIC S9(3)V9(3) COMP-3.    00057700
057800*                                                                 00057800
057900*----- 264 - 267 -----  TAUX DES INT. INTERCAL. / J               00057900
058000       15 SL-RA-DGTTI-FORM-AS-X.                                  00058000
058100          20 SL-RA-DGTTI-FORM-AS        PIC S9(3)V9(3) COMP-3.    00058100
058200*                                                                 00058200
058300*----- 268       -----  EXONÉRATION PM SUR PRIME EMISSION         00058300
058400       15  SL-CO-RVUPR-GDIFAR           PIC X.                    00058400
058500*                                                                 00058500
058600       15  FILLER                 REDEFINES SL-CO-RVUPR-GDIFAR.   00058600
058700          20 CO-PRTI-OORD               PIC X.                    00058700
058800*                                                                 00058800
058900       15  FILLER                 REDEFINES SL-CO-RVUPR-GDIFAR.   00058900
059000          20 SL-CO-RVUPR-OPER           PIC X.                    00059000
059100*                                                                 00059100
059200*----- 269 - 272 -----  PM SUR PRIME EMISSION                     00059200
059300       15 SL-RA-RVUPR-GDIFAR-X.                                   00059300
059400          20 SL-RA-RVUPR-GDIFAR         PIC 99V99.                00059400
059500*                                                                 00059500
059600       15 FILLER                  REDEFINES SL-RA-RVUPR-GDIFAR-X. 00059600
059700          20 SL-RA-RVUPR-OPER           PIC 99V99.                00059700
059800*                                                                 00059800
059900*----- 273 - 276 -----  PM SUR PRIME REMBOURSEMENT                00059900
060000       15 SL-RA-RVTPR-GDIFAR-X.                                   00060000
060100          20 SL-RA-RVTPR-GDIFAR         PIC 99V99.                00060100
060200*                                                                 00060200
060300       15 FILLER                  REDEFINES SL-RA-RVTPR-GDIFAR-X. 00060300
060400          20 SL-RA-RVTPR-OPER           PIC 99V99.                00060400
060500*                                                                 00060500
060600*----- 277 - 287 -----  N° INTERNE VMSU                           00060600
060700       15 NM-ID-010ISSU                 PIC X(11).                00060700
060800*                                                                 00060800
060900*----- 288       -----  TYPE EMISSION INTRODUIT                   00060900
061000       15 CO-ISSUIN-OORD                PIC X.                    00061000
061100*                                                                 00061100
061200*----- 289 - 297 -----  N° SVM                                    00061200
061300       15 NR-ISSUIN-OORD                PIC X(9).                 00061300
061400*                                                                 00061400
061500*----- 298 - 300 -----  RESERVE                                   00061500
061600       15 FILLER                        PIC X(3).                 00061600
061700*                                                                 00061700
061800*+++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++00061800
061900*-----      T I T R E S / D O S S I E R   T I T R E S        -----00061900
062000*           -----------------------------------------             00062000
062100*----- 301 - 380 -----                                            00062100
062200    10 INFO-TITRE.                                                00062200
062300*----- 301 - 313 -----  NO DU TITRE                               00062300
062400       15 NR-ST-FORM-AS                PIC 9(13).                 00062400
062500*                                                                 00062500
062600       15 NR-ST-FORM-AS-R         REDEFINES NR-ST-FORM-AS.        00062600
062700          20 NR-ST-FORM-AS-R1.                                    00062700
062800             25 NR-ST-FORM-AS-P1       PIC 99.                    00062800
062900             25 NR-ST-FORM-AS-P2       PIC 9(3).                  00062900
063000             25 FILLER            REDEFINES NR-ST-FORM-AS-P2.     00063000
063100                30 CT-ID-GOOD-R1       PIC 9.                     00063100
063200                30 CT-DN-GOOD-R1       PIC 9.                     00063200
063300                30 CO-LA-GOOD-R1       PIC 9.                     00063300
063400             25 NR-ST-FORM-AS-P3       PIC 9(7).                  00063400
063500          20 FILLER               REDEFINES NR-ST-FORM-AS-R1.     00063500
063600             25 NR-ST-FORM-AS-R2       PIC 9(12).                 00063600
063700          20 NR-ST-FORM-AS-P4          PIC 9.                     00063700
063800*                                                                 00063800
063900       15 FILLER                  REDEFINES NR-ST-FORM-AS.        00063900
064000          20 NR-ST-MESS-RE             PIC 9(13).                 00064000
064100*                                                                 00064100
064200       15 NR-ST-MESS-RE-R         REDEFINES NR-ST-FORM-AS.        00064200
064300          20 NR-ST-MESS-RE-RD1.                                   00064300
064400             25 NR-ST-MESS-RE-R1           PIC 99.                00064400
064500             25 NR-ST-MESS-RE-R2           PIC 9(3).              00064500
064600             25 NR-ST-MESS-RE-R3        PIC 9(7).                 00064600
064700          20 FILLER               REDEFINES NR-ST-MESS-RE-RD1.    00064700
064800             25 NR-ST-MESS-RE-RD2       PIC 9(12).                00064800
064900          20 NR-ST-MESS-RE-R4           PIC 9.                    00064900
065000*                                                                 00065000
065100       15 FILLER                  REDEFINES NR-ST-FORM-AS.        00065100
065200          20 NR-ST-GDIFC               PIC 9(13).                 00065200
065300*                                                                 00065300
065400       15 NR-ST-OORD-X            REDEFINES NR-ST-FORM-AS.        00065400
065500          20 NR-ST-OORD                PIC 9(13).                 00065500
065600*                                                                 00065600
065700       15 NR-ST-POKB-X            REDEFINES NR-ST-FORM-AS.        00065700
065800          20 NR-ST-POKB                PIC 9(13).                 00065800
065900*                                                                 00065900
066000       15 NR-ST-OPER-X            REDEFINES NR-ST-FORM-AS.        00066000
066100          20 NR-ST-OPER                PIC 9(13).                 00066100
066200*                                                                 00066200
066300       15 NR-ST-COUP-X            REDEFINES NR-ST-FORM-AS.        00066300
066400          20 NR-ST-COUP                PIC 9(13).                 00066400
066500*                                                                 00066500
066600       15 NR-ST-PAY-X             REDEFINES NR-ST-FORM-AS.        00066600
066700          20 NR-ST-PAY                 PIC 9(13).                 00066700
066800*                                                                 00066800
066900*----- 314 - 315 -----  NO DE SEQUENCE DU TITRE                   00066900
067000       15 NS-DB-STOCK-FORM-AS.                                    00067000
067100          20 NS-DB-STOCK-FORM-AS-R      PIC 99.                   00067100
067200*                                                                 00067200
067300       15 FILLER                  REDEFINES NS-DB-STOCK-FORM-AS.  00067300
067400          20 NS-DB-GDIFC                PIC 99.                   00067400
067500*                                                                 00067500
067600       15 FILLER                  REDEFINES NS-DB-STOCK-FORM-AS.  00067600
067700          20 NS-DBST-OORD               PIC 99.                   00067700
067800*                                                                 00067800
067900*----- 316 - 318 -----  NOMBRE DE PAPIER                          00067900
068000       15 NB-ST-MESS-RE.                                          00068000
068100          20 NB-ST-MESS-RE-R            PIC 9(3).                 00068100
068200*                                                                 00068200
068300       15 FILLER                  REDEFINES NB-ST-MESS-RE.        00068300
068400          20 NB-ST-OORD                 PIC 9(3).                 00068400
068500*PV                                                               00068500
068600*                                                                 00068600
068700*----- 319 - 330 -----  NO DOSSIER TITRE                          00068700
068800       15 NR-DS-FORM-AS                 PIC 9(12).                00068800
068900*                                                                 00068900
069000       15 NR-DS-FORM-AS-R         REDEFINES NR-DS-FORM-AS.        00069000
069100          20 NR-DS-FORM-AS-P1           PIC 9(3).                 00069100
069200          20 NR-DS-FORM-AS-P2           PIC 9(7).                 00069200
069300          20 NR-DS-FORM-AS-P3           PIC 9(2).                 00069300
069400*                                                                 00069400
069500       15 NR-SECUR-OORD-X         REDEFINES NR-DS-FORM-AS.        00069500
069600          20 NR-SECUR-OORD              PIC 9(12).                00069600
069700*                                                                 00069700
069800       15 NR-DS-OPER-X            REDEFINES NR-DS-FORM-AS.        00069800
069900          20 NR-DS-OPER                 PIC 9(12).                00069900
070000*                                                                 00070000
070100       15 NR-DS-COUP-X            REDEFINES NR-DS-FORM-AS.        00070100
070200          20 NR-DS-COUP                 PIC 9(12).                00070200
070300*                                                                 00070300
070400       15 NR-DS-PAY-X             REDEFINES NR-DS-FORM-AS.        00070400
070500          20 NR-DS-PAY                  PIC 9(12).                00070500
070600*                                                                 00070600
070700*----- 331 - 342 -----  NO PORTEFEUILLE PORTEUR                   00070700
070800       15 NR-TOOND-OORD-X.                                        00070800
070900          20 NR-TOOND-OORD              PIC 9(12).                00070900
071000*                                                                 00071000
071100*----- 343 - 345 -----  1ER COUPON ATTACHE                        00071100
071200       15 NS-IDCP-FORM-AS-RED.                                    00071200
071300          20 NS-IDCP-FORM-AS            PIC 9(3).                 00071300
071400*                                                                 00071400
071500       15 FILLER                  REDEFINES NS-IDCP-FORM-AS-RED.  00071500
071600          20 NS-RANK-GDIFC              PIC 9(3).                 00071600
071700*                                                                 00071700
071800       15 FILLER                  REDEFINES NS-IDCP-FORM-AS-RED.  00071800
071900          20 NS-IDCP-OORD               PIC 9(3).                 00071900
072000*                                                                 00072000
072100       15 FILLER                  REDEFINES NS-IDCP-FORM-AS-RED.  00072100
072200          20 NS-IDCP-POKB               PIC 9(3).                 00072200
072300*                                                                 00072300
072400       15 FILLER                  REDEFINES NS-IDCP-FORM-AS-RED.  00072400
072500          20 NR-PREMCOUP-OPER           PIC 9(3).                 00072500
072600*                                                                 00072600
072700       15 FILLER                  REDEFINES NS-IDCP-FORM-AS-RED.  00072700
072800          20 NS-RANK-COUP               PIC 9(3).                 00072800
072900*                                                                 00072900
073000*----- 346 - 348 -----  DERNIER COUPON PAYE                       00073000
073100       15 NX-CPFDU-STOCK                PIC 9(3).                 00073100
073200       15 NX-CPAID-STOCK REDEFINES NX-CPFDU-STOCK                 00073200
073300                                        PIC 9(3).                 00073300
073400*                                                                 00073400
073500       15 FILLER                  REDEFINES NX-CPFDU-STOCK.       00073500
073600          20 NS-CPAID-OORD              PIC 9(3).                 00073600
073700*                                                                 00073700
073800*----- 349 - 351 -----  NB DE COUPON DANS LE BLOC                 00073800
073900       15 NB-CPSEQ-GDIFC                PIC 9(3).                 00073900
074000*                                                                 00074000
074100       15 FILLER                  REDEFINES NB-CPSEQ-GDIFC.       00074100
074200          20 NB-CPSEQ-OORD              PIC 9(3).                 00074200
074300*                                                                 00074300
074400       15 FILLER                  REDEFINES NB-CPSEQ-GDIFC.       00074400
074500          20 NB-CPSEQ-COUP              PIC 9(3).                 00074500
074600*                                                                 00074600
074700       15 FILLER                  REDEFINES NB-CPSEQ-GDIFC.       00074700
074800          20 NB-CPSEQ-PAY               PIC 9(3).                 00074800
074900*                                                                 00074900
075000*----- 352 - 355 -----  CD DERNIER COUPON DU BLOC                 00075000
075100       15 NR-CDAG-GDIFC                 PIC 9(4).                 00075100
075200*                                                                 00075200
075300       15 NR-CDAG-OORD-X          REDEFINES NR-CDAG-GDIFC.        00075300
075400          20 NR-CDAG-OORD               PIC 9(4).                 00075400
075500*                                                                 00075500
075600*----- 356       -----  REGIME LINGUISTIQUE                       00075600
075700       15 CO-LA-FORM-AS                 PIC X.                    00075700
075800*                                                                 00075800
075900       15 FILLER                  REDEFINES CO-LA-FORM-AS.        00075900
076000          20 CO-LA-OORD                 PIC X.                    00076000
076100*                                                                 00076100
076200       15 FILLER                  REDEFINES CO-LA-FORM-AS.        00076200
076300          20 CO-LA-POKB                 PIC X.                    00076300
076400*                                                                 00076400
076500*----- 357       -----  CODE CAPITALISATION                       00076500
076600       15 CO-CP-FORM-AS                 PIC X.                    00076600
076700*                                                                 00076700
076800       15 FILLER                  REDEFINES CO-CP-FORM-AS.        00076800
076900          20 CO-CP-OORD                 PIC X.                    00076900
077000*                                                                 00077000
077100*----- 358       -----  TYPE NO TITRE INTRODUIT                   00077100
077200       15 CO-STIN-OORD                  PIC X(1).                 00077200
077300*                                                                 00077300
077400*----- 359 - 372 -----  NO TITRE INTRODUIT                        00077400
077500       15 NR-STIN-OORD                  PIC X(14).                00077500
077600*                                                                 00077600
077700*----- 373 - 380 -----  RESERVE                                   00077700
077800       15 FILLER                        PIC X(8).                 00077800
077900*                                                                 00077900
078000*+++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++00078000
078100*-----      M O N T A N T S                                  -----00078100
078200*           ---------------                                       00078200
078300*----- 381 - 510 -----                                            00078300
078400    10 INFO-MT.                                                   00078400
078500*                                                                 00078500
078600*----- 381 - 388 -----  NOMINAL                                   00078600
078700       15 AM-CNS-FORM-AS-R.                                       00078700
078800          20 AM-CNS-FORM-AS             PIC S9(13)V9(2) COMP-3.   00078800
078900*                                                                 00078900
079000       15 FILLER                  REDEFINES AM-CNS-FORM-AS-R.     00079000
079100          20 AM-CNS-OORD                PIC S9(13)V9(2) COMP-3.   00079100
079200*                                                                 00079200
079300       15 FILLER                  REDEFINES AM-CNS-FORM-AS-R.     00079300
079400          20 AM-CNS-POKB                PIC S9(13)V9(2) COMP-3.   00079400
079500*                                                                 00079500
079600       15 FILLER                  REDEFINES AM-CNS-FORM-AS-R.     00079600
079700          20 AM-CND-GDIFC               PIC S9(13)V9(2) COMP-3.   00079700
079800*                                                                 00079800
079900       15 FILLER                  REDEFINES AM-CNS-FORM-AS-R.     00079900
080000          20 AM-CNS-OPER                PIC S9(13)V9(2) COMP-3.   00080000
080100*                                                                 00080100
080200       15 FILLER                  REDEFINES AM-CNS-FORM-AS-R.     00080200
080300          20 AM-CND-COUP                PIC S9(13)V9(2) COMP-3.   00080300
080400*                                                                 00080400
080500       15 FILLER                  REDEFINES AM-CNS-FORM-AS-R.     00080500
080600          20 AM-CNS-COUP                PIC S9(13)V9(2) COMP-3.   00080600
080700*                                                                 00080700
080800*----- 389 - 396 -----  MONTANT DE LA PRIME D'EMISSION            00080800
080900       15 AM-PS-FORM-AS-R.                                        00080900
081000          20 AM-PS-FORM-AS              PIC S9(13)V9(2) COMP-3.   00081000
081100*                                                                 00081100
081200       15 FILLER                  REDEFINES AM-PS-FORM-AS-R.      00081200
081300          20 AM-PS-OORD                 PIC S9(13)V9(2) COMP-3.   00081300
081400*                                                                 00081400
081500       15 FILLER                  REDEFINES AM-PS-FORM-AS-R.      00081500
081600          20 AM-PS-OPER                 PIC S9(13)V9(2) COMP-3.   00081600
081700*                                                                 00081700
081800       15 FILLER                  REDEFINES AM-PS-FORM-AS-R.      00081800
081900          20 AM-PSB-OPER                PIC S9(13)V9(2) COMP-3.   00081900
082000*                                                                 00082000
082100*----- 397 - 404 -----  REMBOURSABLE BRUT                         00082100
082200       15 AM-CND-FORM-AS-R.                                       00082200
082300          20 AM-CND-FORM-AS             PIC S9(13)V9(2) COMP-3.   00082300
082400*                                                                 00082400
082500       15 FILLER                  REDEFINES AM-CND-FORM-AS-R.     00082500
082600          20 AM-CND-OORD                PIC S9(13)V9(2) COMP-3.   00082600
082700*                                                                 00082700
082800       15 FILLER                  REDEFINES AM-CND-FORM-AS-R.     00082800
082900          20 AM-CND-OPER                PIC S9(13)V9(2) COMP-3.   00082900
083000*                                                                 00083000
083100*----- 405 - 412 -----  REMBOURSABLE NET                          00083100
083200       15 AM-CNDN-FORM-AS-R.                                      00083200
083300          20 AM-CNDN-FORM-AS            PIC S9(13)V9(2) COMP-3.   00083300
083400*                                                                 00083400
083500       15 FILLER                  REDEFINES AM-CNDN-FORM-AS-R.    00083500
083600          20 AM-CNDN-OORD               PIC S9(13)V9(2) COMP-3.   00083600
083700*                                                                 00083700
083800*----- 413 - 420 -----  MT INTERETS DES COUPONS                   00083800
083900       15 AM-INTER-FORM-AS-R.                                     00083900
084000          20 AM-INTER-FORM-AS           PIC S9(13)V9(2) COMP-3.   00084000
084100*                                                                 00084100
084200       15 FILLER                  REDEFINES AM-INTER-FORM-AS-R.   00084200
084300          20 AM-INTER-OORD              PIC S9(13)V9(2) COMP-3.   00084300
084400*                                                                 00084400
084500       15 FILLER                  REDEFINES AM-INTER-FORM-AS-R.   00084500
084600          20 AM-INTGR-GDIFC             PIC S9(13)V9(2) COMP-3.   00084600
084700*                                                                 00084700
084800       15 FILLER                  REDEFINES AM-INTER-FORM-AS-R.   00084800
084900          20 AM-INTGR-COUP              PIC S9(13)V9(2) COMP-3.   00084900
085000*                                                                 00085000
085100*----- 421 - 428 -----  MONTANT DES COUTS LORS DU PUT             00085100
085200       15 SL-AM-PUT-GDIFAR-X.                                     00085200
085300          20 SL-AM-PUT-GDIFAR           PIC S9(13)V9(2) COMP-3.   00085300
085400*                                                                 00085400
085500       15 FILLER                  REDEFINES SL-AM-PUT-GDIFAR-X.   00085500
085600          20 AM-PUT-OORD                PIC S9(13)V9(2) COMP-3.   00085600
085700*                                                                 00085700
085800       15 FILLER                  REDEFINES SL-AM-PUT-GDIFAR-X.   00085800
085900          20 SL-AM-PUT-OPER             PIC S9(13)V9(2) COMP-3.   00085900
086000*                                                                 00086000
086100*----- 429 - 436 -----  PRIME DE REMBOURSEMENT                    00086100
086200       15 SL-AM-TPREM-GDIFAR-X.                                   00086200
086300          20 SL-AM-TPREM-GDIFAR         PIC S9(13)V9(2) COMP-3.   00086300
086400*                                                                 00086400
086500       15 FILLER                  REDEFINES SL-AM-TPREM-GDIFAR-X. 00086500
086600          20 AM-TPREM-OORD              PIC S9(13)V9(2) COMP-3.   00086600
086700*                                                                 00086700
086800       15 FILLER                  REDEFINES SL-AM-TPREM-GDIFAR-X. 00086800
086900          20 SL-AM-TPREM-OPER           PIC S9(13)V9(2) COMP-3.   00086900
087000*                                                                 00087000
087100*----- 437 - 444 -----  PRIME DE SOUSCRIPTION                     00087100
087200       15 SL-AM-UPREM-GDIFAR-X.                                   00087200
087300          20 SL-AM-UPREM-GDIFAR         PIC S9(13)V9(2) COMP-3.   00087300
087400*                                                                 00087400
087500       15 FILLER                  REDEFINES SL-AM-UPREM-GDIFAR-X. 00087500
087600          20 AM-UPREM-OORD              PIC S9(13)V9(2) COMP-3.   00087600
087700*                                                                 00087700
087800       15 FILLER                  REDEFINES SL-AM-UPREM-GDIFAR-X. 00087800
087900          20 SL-AM-UPREM-OPER           PIC S9(13)V9(2) COMP-3.   00087900
088000*                                                                 00088000
088100*----- 445 - 452 -----  INTÉRÊTS BRUT DU BLOC DE COUPON           00088100
088200       15 AM-INB-GDIFC                  PIC S9(13)V9(2) COMP-3.   00088200
088300*                                                                 00088300
088400       15 FILLER                  REDEFINES AM-INB-GDIFC.         00088400
088500          20 AM-INB-OORD                PIC S9(13)V9(2) COMP-3.   00088500
088600                                                                  00088600
088700*                                                                 00088700
088800*----- 453 - 460 -----  INTÉRÊTS CAP DU BLOC DE COUPON            00088800
088900       15 AM-INBCA-GDIFC                PIC S9(13)V9(2) COMP-3.   00088900
089000*                                                                 00089000
089100       15 FILLER                  REDEFINES AM-INBCA-GDIFC.       00089100
089200          20 AM-INBCA-OORD              PIC S9(13)V9(2) COMP-3.   00089200
089300*                                                                 00089300
089400       15 FILLER                  REDEFINES AM-INBCA-GDIFC.       00089400
089500          20 AM-INBCA-COUP              PIC S9(13)V9(2) COMP-3.   00089500
089600*                                                                 00089600
089700*----- 461 - 468 -----  MONTANT NET DE L'OPERATION                00089700
089800       15 AM-CNSN-FORM-AS-R.                                      00089800
089900          20 AM-CNSN-FORM-AS            PIC S9(13)V9(2) COMP-3.   00089900
090000*            ( REDEFINITION POUR REMBOURSEMENT ET RACHAT )        00090000
090100       15 FILLER  REDEFINES AM-CNSN-FORM-AS-R.                    00090100
090200          20 AM-CRN-FORM-AS             PIC S9(13)V9(2) COMP-3.   00090200
090300*                                                                 00090300
090400       15 FILLER  REDEFINES AM-CNSN-FORM-AS-R.                    00090400
090500          20 AM-CNSN-OORD               PIC S9(13)V9(2) COMP-3.   00090500
090600*                                                                 00090600
090700       15 FILLER  REDEFINES AM-CNSN-FORM-AS-R.                    00090700
090800          20 AM-CNSN-OPER               PIC S9(13)V9(2) COMP-3.   00090800
090900*                                                                 00090900
091000*----- 469 - 476 -----  MONTANT NET DE LA TRANSACTION             00091000
091100       15 AM-CNSNTRN-OORD               PIC S9(13)V9(2) COMP-3.   00091100
091200*                                                                 00091200
091300       15 FILLER                  REDEFINES AM-CNSNTRN-OORD.      00091300
091400          20 AM-INNET-GDIFC             PIC S9(13)V9(2) COMP-3.   00091400
091500*                                                                 00091500
091600*----- 477 - 484 -----  TOTAL NOMINAL DE LA TRANSACTION           00091600
091700       15 AM-CNSTRAN-OORD               PIC S9(13)V9(2) COMP-3.   00091700
091800*                                                                 00091800
091900       15 AM-CNSSP-FORM-AS-RED    REDEFINES AM-CNSTRAN-OORD.      00091900
092000          20 AM-CNSSP-FORM-AS           PIC S9(13)V9(2) COMP-3.   00092000
092100*                                                                 00092100
092200*----- 485 - 492 -----  TOTAL BRUT DE LA TRANSACTION              00092200
092300       15 AM-CNSBTRN-OORD               PIC S9(13)V9(2) COMP-3.   00092300
092400*                                                                 00092400
092500       15 FILLER                  REDEFINES AM-CNSBTRN-OORD.      00092500
092600          20 AM-INGRT-FORM-AS           PIC S9(13)V9(2) COMP-3.   00092600
092700*                                                                 00092700
092800*                                                                 00092800
092900*----- 493 - 510 -----  RESERVE                                   00092900
093000       15 FILLER                        PIC X(18).                00093000
093100*                                                                 00093100
093200*+++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++00093200
093300*-----      T T I                                            -----00093300
093400*           -----                                                 00093400
093500*----- 511 - 550 -----                                            00093500
093600    10 INFO-TTI.                                                  00093600
093700*----- 511 - 518 -----  MONTANT DES QZ INTERCAL.                  00093700
093800       15 AM-FIN-FORM-AS-R.                                       00093800
093900          20 AM-FIN-FORM-AS             PIC S9(13)V9(2) COMP-3.   00093900
094000*                                                                 00094000
094100       15 FILLER                  REDEFINES AM-FIN-FORM-AS-R.     00094100
094200          20 AM-FIN-OORD                PIC S9(13)V9(2) COMP-3.   00094200
094300*                                                                 00094300
094400       15 FILLER                  REDEFINES AM-FIN-FORM-AS-R.     00094400
094500          20 AM-FIN-OPER                PIC S9(13)V9(2) COMP-3.   00094500
094600*                                                                 00094600
094700*----- 519 - 521 -----  NB DE QUINZAINES INTERCALAIRES            00094700
094800       15 NB-FI-FORM-AS-R.                                        00094800
094900          20 NB-FI-FORM-AS              PIC 999.                  00094900
095000*                                                                 00095000
095100       15 FILLER                  REDEFINES NB-FI-FORM-AS-R.      00095100
095200          20 NB-FI-OORD                 PIC 999.                  00095200
095300*                                                                 00095300
095400       15 FILLER                  REDEFINES NB-FI-FORM-AS-R.      00095400
095500          20 NB-FI-OPER                 PIC 999.                  00095500
095600*                                                                 00095600
095700*----- 522 - 529 -----  MT DES INT. INTERC. JOURN.                00095700
095800       15 SL-AM-DGTTI-FORM-AS-X.                                  00095800
095900          20 SL-AM-DGTTI-FORM-AS        PIC S9(13)V9(2) COMP-3.   00095900
096000*                                                                 00096000
096100       15 FILLER                  REDEFINES SL-AM-DGTTI-FORM-AS-X.00096100
096200          20 AM-DGTTI-OORD              PIC S9(13)V9(2) COMP-3.   00096200
096300*                                                                 00096300
096400       15 FILLER                  REDEFINES SL-AM-DGTTI-FORM-AS-X.00096400
096500          20 SL-AM-DGTTI-OPER           PIC S9(13)V9(2) COMP-3.   00096500
096600*                                                                 00096600
096700*----- 530 - 531 -----  NB JOURS INT. INTERCAL.                   00096700
096800       15 SL-NB-DGTTI-FORM-AS-X.                                  00096800
096900          20 SL-NB-DGTTI-FORM-AS        PIC 9(2).                 00096900
097000*                                                                 00097000
097100       15 FILLER                  REDEFINES SL-NB-DGTTI-FORM-AS-X.00097100
097200          20 NB-DGTTI-OORD              PIC 9(2).                 00097200
097300*                                                                 00097300
097400       15 FILLER                  REDEFINES SL-NB-DGTTI-FORM-AS-X.00097400
097500          20 SL-NB-DGTTI-OPER           PIC 9(2).                 00097500
097600*                                                                 00097600
097700*----- 532       -----  INT. INTERC. JOURN. SUR BUDGET AGENT      00097700
097800       15 SL-ST-DGTTI-FORM-AS-X.                                  00097800
097900          20 SL-ST-DGTTI-FORM-AS        PIC 9.                    00097900
098000*                                                                 00098000
098100       15 FILLER                  REDEFINES SL-ST-DGTTI-FORM-AS-X.00098100
098200          20 ST-DGTTI-OORD              PIC 9.                    00098200
098300*                                                                 00098300
098400*----- 533 - 550 -----  RESERVE                                   00098400
098500       15 FILLER                        PIC X(18).                00098500
098600*                                                                 00098600
098700*+++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++00098700
098800*-----    I N F O  D I (COUPURES/DOC. PRINCIP)    -----           00098800
098900*         ------------------------------------                    00098900
099000*----- 551 - 580 -----                                            00099000
099100    10 INFO-DI.                                                   00099100
099200*                                                                 00099200
099300*----- 551 - 556 -----  DOCUMENT DE TETE                          00099300
099400       15 NR-FIGRP-FORM-AS-R.                                     00099400
099500          20 NR-FIGRP-FORM-AS           PIC 9(6).                 00099500
099600*                                                                 00099600
099700       15 FILLER                  REDEFINES NR-FIGRP-FORM-AS-R.   00099700
099800          20 NR-FIGRP-OPER              PIC 9(6).                 00099800
099900*                                                                 00099900
100000*----- 557 - 562 -----  DOCUMENT SUIVANT                          00100000
100100       15 NR-NEGRP-FORM-AS-R.                                     00100100
100200          20 NR-NEGRP-FORM-AS           PIC 9(6).                 00100200
100300*                                                                 00100300
100400*----- 563 - 568 -----  DOCUMENT PRECEDENT                        00100400
100500       15 NR-PRGRP-FORM-AS-R.                                     00100500
100600          20 NR-PRGRP-FORM-AS           PIC 9(6).                 00100600
100700*                                                                 00100700
100800*----- 569 - 574 -----  DI MODIFIE OU NOUVEAU DI POUR ORDRE ECH.  00100800
100900       15 NEW-NR-ID-OMR.                                          00100900
101000          20 NEW-NR-ID-OMR-R            PIC 9(6).                 00101000
101100       15 NR-ID-2-RETRAIT-R       REDEFINES NEW-NR-ID-OMR.        00101100
101200          20 NR-ID-2-RETRAIT            PIC 9(6).                 00101200
101300*                                                                 00101300
101400*----- 575 - 580 -----                                            00101400
101500       15 FILLER                        PIC X(6).                 00101500
101600*                                                                 00101600
101700*+++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++00101700
101800*-----             R E G U L .                               -----00101800
101900*                  -----------                                    00101900
102000*----- 581 - 605 -----                                            00102000
102100    10 INFO-REGUL.                                                00102100
102200*                                                                 00102200
102300*----- 581 - 593 -----  NOUVEAU NO DE TITRE                       00102300
102400       15 NR-STNEW-GDIFRV.                                        00102400
102500          20 NR-STNEW-GDIFRV-NUM        PIC 9(13).                00102500
102600*                                                                 00102600
102700       15 NR-STNEW-GDIFRV-R       REDEFINES NR-STNEW-GDIFRV.      00102700
102800          20 NR-STNEW-GDIFRV-R1.                                  00102800
102900             25 NR-STNEW-GDIFRV-P1      PIC 99.                   00102900
103000             25 NR-STNEW-GDIFRV-P2      PIC 9(3).                 00103000
103100             25 FILLER        REDEFINES NR-STNEW-GDIFRV-P2.       00103100
103200                30 CT-ID-GOOD-NEW-R1    PIC 9.                    00103200
103300                30 CT-DN-GOOD-NEW-R1    PIC 9.                    00103300
103400                30 CO-LA-GOOD-NEW-R1    PIC 9.                    00103400
103500             25 NR-STNEW-GDIFRV-P3      PIC 9(7).                 00103500
103600          20 FILLER               REDEFINES NR-STNEW-GDIFRV-R1.   00103600
103700             25 NR-STNEW-GDIFRV-R2      PIC 9(12).                00103700
103800          20 NR-STNEW-GDIFRV-P4         PIC 9.                    00103800
103900*                                                                 00103900
104000       15 NR-STNEW-OORD-X         REDEFINES NR-STNEW-GDIFRV.      00104000
104100          20 NR-STNEW-OORD              PIC 9(13).                00104100
104200*                                                                 00104200
104300       15 NR-STNEW-POKB-X         REDEFINES NR-STNEW-GDIFRV.      00104300
104400          20 NR-STNEW-POKB              PIC 9(13).                00104400
104500*                                                                 00104500
104600       15 NR-STNEW-GDIFRV-OPER-X  REDEFINES NR-STNEW-GDIFRV.      00104600
104700          20 NR-STNEW-GDIFRV-OPER       PIC 9(13).                00104700
104800*                                                                 00104800
104900*----- 594 - 595 -----  NO SEQUENCE DU NOUVEAU TITRE              00104900
105000       15 NS-DB-STOCK-GDIFRV            PIC X(02).                00105000
105100*                                                                 00105100
105200       15 FILLER                  REDEFINES NS-DB-STOCK-GDIFRV.   00105200
105300          20 NS-DBSTNEW-OORD            PIC 9(2).                 00105300
105400*                                                                 00105400
105500*----- 596 - 598 -----  DERNIER COUPON PAYE                       00105500
105600       15 NS-CPAID-GDIFRV-RED.                                    00105600
105700          20 NS-CPAID-GDIFRV            PIC 9(3).                 00105700
105800*                                                                 00105800
105900       15 FILLER                  REDEFINES NS-CPAID-GDIFRV-RED.  00105900
106000          20 NS-CPAIDNW-OORD            PIC 9(3).                 00106000
106100*                                                                 00106100
106200       15 FILLER                  REDEFINES NS-CPAID-GDIFRV-RED.  00106200
106300          20 NS-CPAID-GDIFRV-OPER       PIC 9(3).                 00106300
106400*                                                                 00106400
106500*----- 599 - 602 -----  CD DERNIER COUPON PAYE                    00106500
106600       15 NR-CDCP-GDIFRV-RED.                                     00106600
106700          20 NR-CDCP-GDIFRV             PIC 9(4).                 00106700
106800*                                                                 00106800
106900       15 NR-CDCPNEW-OORD-X       REDEFINES NR-CDCP-GDIFRV-RED.   00106900
107000          20 NR-CDCPNEW-OORD            PIC 9(4).                 00107000
107100*                                                                 00107100
107200*----- 603 - 605 -----                                            00107200
107300       15 FILLER                        PIC X(3).                 00107300
107400*                                                                 00107400
107500*+++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++00107500
107600*-----      T O B - T F E - F L K  (TAXES)                        00107600
107700*           ----------------------                                00107700
107800*----- 606 - 680 -----                                            00107800
107900    10 INFO-TAX.                                                  00107900
108000*                                                                 00108000
108100*----- 606       -----  EXONÉRATION  TOB (' '=PAS/'0'=NON/'1'=OUI)00108100
108200       15 CO-EXTOB-FORM-AS              PIC X(01).                00108200
108300*                                                                 00108300
108400       15 FILLER                  REDEFINES CO-EXTOB-FORM-AS.     00108400
108500          20 CO-EXTOB-OORD              PIC X(01).                00108500
108600*                                                                 00108600
108700*----- 607       -----  PLAFOND TOB ('0'=NON/'1'=OUI)             00108700
108800       15 CO-PLTOB-FORM-AS              PIC X(01).                00108800
108900*                                                                 00108900
109000       15 FILLER                  REDEFINES CO-PLTOB-FORM-AS.     00109000
109100          20 CO-PLTOB-OORD              PIC X(01).                00109100
109200*                                                                 00109200
109300*----- 608 - 611 -----  TAUX TOB                                  00109300
109400       15 RA-TOB-FORM-AS-X.                                       00109400
109500          20 RA-TOB-FORM-AS             PIC S999V999 COMP-3.      00109500
109600*                                                                 00109600
109700       15 FILLER                  REDEFINES RA-TOB-FORM-AS-X.     00109700
109800          20 RA-TOB-OORD                PIC S999V999 COMP-3.      00109800
109900*                                                                 00109900
110000*----- 612 - 619 -----  MT TOB                                    00110000
110100       15 AM-TOB-FORM-AS-X.                                       00110100
110200          20 AM-TOB-FORM-AS             PIC S9(13)V9(2) COMP-3.   00110200
110300*                                                                 00110300
110400       15 FILLER                  REDEFINES AM-TOB-FORM-AS-X.     00110400
110500          20 AM-TOB-OORD                PIC S9(13)V9(2) COMP-3.   00110500
110600*                                                                 00110600
110700       15 FILLER                  REDEFINES AM-TOB-FORM-AS-X.     00110700
110800          20 SL-AM-TAX-OPER             PIC S9(13)V9(2) COMP-3.   00110800
110900*                                                                 00110900
111000*----- 620       -----  EXONÉRATION  TFE (' '=PAS/'0'=NON/'1'=OUI)00111000
111100       15 CO-EXTFE-FORM-AS              PIC X(01).                00111100
111200*                                                                 00111200
111300       15 FILLER                  REDEFINES CO-EXTFE-FORM-AS.     00111300
111400          20 CO-EXTFE-OORD              PIC X(01).                00111400
111500*                                                                 00111500
111600*----- 621 - 624 -----  TAUX TFE                                  00111600
111700       15 RA-TARPH-FORM-AS-X.                                     00111700
111800          20 RA-TARPH-FORM-AS           PIC S999V999 COMP-3.      00111800
111900*                                                                 00111900
112000       15 FILLER                  REDEFINES RA-TARPH-FORM-AS-X.   00112000
112100          20 RA-TARPH-OORD              PIC S999V999 COMP-3.      00112100
112200*                                                                 00112200
112300*----- 625 - 632 -----  MT TFE                                    00112300
112400       15 AM-TARPH-FORM-AS-X.                                     00112400
112500          20 AM-TARPH-FORM-AS           PIC S9(13)V9(2) COMP-3.   00112500
112600*                                                                 00112600
112700       15 FILLER                  REDEFINES AM-TARPH-FORM-AS-X.   00112700
112800          20 AM-TARPH-OORD              PIC S9(13)V9(2) COMP-3.   00112800
112900*                                                                 00112900
113000       15 FILLER                  REDEFINES AM-TARPH-FORM-AS-X.   00113000
113100          20 AM-TARPH-OPER              PIC S9(13)V9(2) COMP-3.   00113100
113200*                                                                 00113200
113300*----- 633 - 640 -----  MT BASE CALCUL TOB TFE                    00113300
113400       15 AM-BASE-FORM-AS-X.                                      00113400
113500          20 AM-BASE-FORM-AS            PIC S9(13)V9(2) COMP-3.   00113500
113600*                                                                 00113600
113700       15 FILLER                  REDEFINES AM-BASE-FORM-AS-X.    00113700
113800          20 AM-BASE-OORD               PIC S9(13)V9(2) COMP-3.   00113800
113900*                                                                 00113900
114000       15 FILLER                  REDEFINES AM-BASE-FORM-AS-X.    00114000
114100          20 AM-BASE-OPER               PIC S9(13)V9(2) COMP-3.   00114100
114200*                                                                 00114200
114300*----- 641       -----  EXONÉRATION  TFE (' '=PAS/'0'=NON/'1'=OUI)00114300
114400       15 CO-EXFLK-OORD                 PIC X(01).                00114400
114500*                                                                 00114500
114600*----- 642 - 644 -----  MT LIVRAISON PHYSIQUE AU CLIENT           00114600
114700       15 AM-FLK-FORM-AS-X.                                       00114700
114800          20 AM-FLK-FORM-AS             PIC S9(3)V9(2)  COMP-3.   00114800
114900*                                                                 00114900
115000       15 FILLER                  REDEFINES AM-FLK-FORM-AS-X.     00115000
115100          20 AM-FLK-OORD                PIC S9(3)V9(2)  COMP-3.   00115100
115200*                                                                 00115200
115300       15 FILLER                  REDEFINES AM-FLK-FORM-AS-X.     00115300
115400          20 AM-FLK-OPER                PIC S9(3)V9(2)  COMP-3.   00115400
115500*                                                                 00115500
115600*----- 645 - 652 -----  MT COMMISSION DEXIA (RACHATS)             00115600
115700       15 AM-COMDEX-OORD                PIC S9(13)V9(2)  COMP-3.  00115700
115800*                                                                 00115800
115900       15 FILLER                  REDEFINES AM-COMDEX-OORD.       00115900
116000          20 AM-COMM-OPER               PIC S9(13)V9(2)  COMP-3.  00116000
116100*                                                                 00116100
116200*----- 653 - 660 -----  MT COMMISSION AGENT (RACHATS)             00116200
116300       15 AM-COMAG-OORD                 PIC S9(13)V9(2)  COMP-3.  00116300
116400*                                                                 00116400
116500*----- 661 - 679 -----  RESERVE                                   00116500
116600       15 FILLER                        PIC X(19).                00116600
116700*                                                                 00116700
116800*+++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++  00116800
116900*----          I N F O S    P I C                         -----   00116900
117000*              ------------------                                 00117000
117100*----- 680 - 739 -----                                            00117100
117200    10 INFO-PIC.                                                  00117200
117300*                                                                 00117300
117400*----- 680 - 695 -----  N° REFERENCE VISITE CLIENT                00117400
117500       15 NR-CONTACT-OORD               PIC X(16).                00117500
117600*                                                                 00117600
117700*----- 696 - 705 -----  PERSONNE DE CONTACT                       00117700
117800       15 NR-IDACTCT-OORD               PIC X(10).                00117800
117900*                                                                 00117900
118000*----- 706 - 715 -----  CLIENT 1                                  00118000
118100       15 NR-IDACT1-OORD                PIC X(10).                00118100
118200*                                                                 00118200
118300       15 FILLER                  REDEFINES NR-IDACT1-OORD.       00118300
118400          20 NR-IDACT1-POKB             PIC X(10).                00118400
118500*                                                                 00118500
118600*----- 716 - 725 -----  CLIENT 2                                  00118600
118700       15 NR-IDACT2-OORD                PIC X(10).                00118700
118800*                                                                 00118800
118900       15 FILLER                  REDEFINES NR-IDACT2-OORD.       00118900
119000          20 NR-IDACT2-POKB             PIC X(10).                00119000
119100*                                                                 00119100
119200*----- 726       -----  TYPE DE CONTACT                           00119200
119300       15 CO-TCONTAC-OORD               PIC X.                    00119300
119400*                                                                 00119400
119500*----- 727       -----  CODE NON RESIDENT                         00119500
119600       15 CO-EXPM-OORD                  PIC X.                    00119600
119700*                                                                 00119700
119800*----- 728 - 731 -----  TAUX DE PRECOMPTE                         00119800
119900       15 RA-TI-FORM-AS-R.                                        00119900
120000          20 RA-TI-FORM-AS              PIC 99V99.                00120000
120100*                                                                 00120100
120200       15 FILLER                  REDEFINES RA-TI-FORM-AS-R.      00120200
120300          20 RA-TI-GDIFC                PIC 99V99.                00120300
120400*                                                                 00120400
120500       15 FILLER                  REDEFINES RA-TI-FORM-AS-R.      00120500
120600          20 RA-TI-OORD                 PIC 99V99.                00120600
120700*                                                                 00120700
120800       15 FILLER                  REDEFINES RA-TI-FORM-AS-R.      00120800
120900          20 RA-TI-OPER                 PIC 99V99.                00120900
121000*                                                                 00121000
121100       15 FILLER                  REDEFINES RA-TI-FORM-AS-R.      00121100
121200          20 RA-TI-COUP                 PIC 99V99.                00121200
121300*                                                                 00121300
121400       15 FILLER                  REDEFINES RA-TI-FORM-AS-R.      00121400
121500          20 RA-TI-PAY                  PIC 99V99.                00121500
121600*                                                                 00121600
121100*----- 732 - 732 ----- CODE TAXE DI RUPO                          00121810
121200       15 CO-TDR                        PIC X(1).                 00121820
                                                                        00121830
121100*----- 733 - 735 ----- TAUX THEORIQUE TAXE DI RUPO                00121840
121200       15 RA-TDR                        PIC S9(2)V9(2) COMP-3.    00121850
                                                                        00121860
      *----- 736 - 736 ----- CODE FATCA                                 00121861
             15 CO-FATCA-OORD                 PIC X(1).                 00121862
121100*----- 737 - 739 -----                                            00121870
121200       15 FILLER                        PIC X(3).                 00121880
121900*                                                                 00121900
122000*+++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++  00122000
122100*----          R E F E R E N C E S                        -----   00122100
122200*              -------------------                                00122200
122300*----- 740 - 879 -----                                            00122300
122400    10 INFO-REF.                                                  00122400
122500*                                                                 00122500
122600*----- 740 - 765 -----  REFERENCE CUSTODY                         00122600
122700       15 NR-REFCUST-OORD               PIC X(26).                00122700
122800*                                                                 00122800
122900*----- 766 - 791 -----  TIMESTAMP REF CUSTODY                     00122900
123000       15 TS-EVTCUST-OORD               PIC X(26).                00123000
123100*                                                                 00123100
123200*----- 792 - 796 -----  N°SOLDE CUSTODY                           00123200
123300       15 NS-IDSAL-OORD                 PIC S9(8) COMP-3.         00123300
123400*                                                                 00123400
123500*----- 797 - 803 -----  NO DU TR                                  00123500
123600       15 NR-TR-FORM-AS-R.                                        00123600
123700          20 NR-TR-FORM-AS-1-6          PIC 9(6).                 00123700
123800          20 NR-TR-CD                   PIC 9.                    00123800
123900*                                                                 00123900
124000       15 FILLER                  REDEFINES NR-TR-FORM-AS-R.      00124000
124100          20 NR-TR-FORM-AS              PIC 9(7).                 00124100
124200*                                                                 00124200
124300       15 FILLER                  REDEFINES NR-TR-FORM-AS-R.      00124300
124400          20 NR-TR-OORD                 PIC 9(7).                 00124400
124500*                                                                 00124500
124600       15 FILLER                  REDEFINES NR-TR-FORM-AS-R.      00124600
124700          20 NR-RTR-OPER                PIC 9(7).                 00124700
124800*                                                                 00124800
124900*----- 804 - 808 -----  N° REF FISCALE                            00124900
125000       15 NS-REFFISC-OORD               PIC 9(9) COMP-3.          00125000
125100*                                                                 00125100
125200       15 FILLER                  REDEFINES NS-REFFISC-OORD.      00125200
125300           20 NS-TAX-OPER               PIC 9(9) COMP-3.          00125300
125400*                                                                 00125400
125500*----- 809 - 810 -----  TYPE COMPTE LIQUIDATION                   00125500
125600       15 CO-TVEREF-OORD                PIC X(2).                 00125600
125700*                                                                 00125700
125800*----- 811 - 822 -----  N° COMPTE LIQUIDATION                     00125800
125900       15 NR-ACCVER-OORD                PIC X(12).                00125900
126000*                                                                 00126000
126100*----- 823 - 831 -----  N° CAISSE LIQUIDATION CASH                00126100
126200       15 NR-KASV-OORD                  PIC X(9).                 00126200
126300*                                                                 00126300
126400*----- 832 - 857 -----  N° REFERENCE AOM                          00126400
126500       15 NR-REFAOM-OORD                PIC X(26).                00126500
126600*                                                                 00126600
126700*                                                                 00126700
126800*----- 858 - 862 -----  N° REFERENCE PHYSICAL MANAGEMENT          00126800
126900       15 NS-REF-PFLX                   PIC S9(9) COMP-3.         00126900
127000*                                                                 00127000
      *----- 863 - 878 -----  NR-REFINT-074DORD                         00127010
             15 NR-REFINT-074DORD             PIC X(16).                00127020
      *                                                                 00127030
127100*----- 879 - 879 -----  FILLER                                    00127100
127200       15 FILLER                        PIC X(1).                 00127200
127300*                                                                 00127300
127400*+++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++  00127400
127500*----          S T A T U S                               -----    00127500
127600*              -----------                                        00127600
127700*----- 880 - 899 -----                                            00127700
127800    10 INFO-STATUS.                                               00127800
127900*                                                                 00127900
128000*----- 880       -----  STATUS RESERVATION AOM                    00128000
128100       15 CO-STRAOM-OORD                PIC X.                    00128100
128200*                                                                 00128200
128300*----- 881       -----  STATUS CONFIRMATION AOM                   00128300
128400       15 CO-STCAOM-OORD                PIC X.                    00128400
128500*                                                                 00128500
128600*----- 882       -----  STATUS RESERVATION CUSTODY                00128600
128700       15 CO-STRCUST-OORD               PIC X.                    00128700
128800*                                                                 00128800
128900*----- 883       -----  STATUS CONFIRMATION CUSTODY               00128900
129000       15 CO-STCCUST-OORD               PIC X.                    00129000
129100*                                                                 00129100
129200*----- 884       -----  STATUS PRINT AU SIEGE                     00129200
129300       15 CO-STPRINT-OORD               PIC X.                    00129300
129400*                                                                 00129400
129500       15 FILLER                  REDEFINES CO-STPRINT-OORD.      00129500
129600          20 CO-STPRINT-POKB            PIC X.                    00129600
129700*                                                                 00129700
129800*----- 885       -----  STATUS CIRCULATION                        00129800
129900       15 CO-STCIRC-OORD                PIC X.                    00129900
130000*                                                                 00130000
130100*----- 886       -----  STATUS COMPTABILISE                       00130100
130200       15 CO-STACCT-OORD                PIC X.                    00130200
130300*                                                                 00130300
130400*----- 887       -----  STATUS TRAITEMENT BATCH                   00130400
130500       15 CO-STBATCH-OORD               PIC X.                    00130500
130600*                                                                 00130600
130700*----- 888       -----  STATUS CONTROLE SIGNATURE NÉCESSAIRE      00130700
130800       15 ST-SGNNEC-OORD                PIC X.                    00130800
130900*                                                                 00130900
131000*----- 889       -----  STATUS CONTROLE SIGNATURE EXÉCUTÉ         00131000
131100       15 ST-SGNOK-OORD                 PIC X.                    00131100
131200*----- 890       -----  STATUS REMBOURSEMENT                      00131200
131300       15 CO-STREMB                     PIC X.                    00131300
131400*                                                                 00131400
131500*----- 891 - 899 -----                                            00131500
131600       15 FILLER                        PIC X(09).                00131600
131700*                                                                 00131700
131800*+++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++  00131800
131900*----          M E S S A G E S                           -----    00131900
132000*              ---------------                                    00132000
132100*----- 900 -     -----                                            00132100
132200    10 INFO-MESS.                                                 00132200
132300*                                                                 00132300
132400*----- 900 -     -----  TYPE ERREUR                               00132400
132500       15 CO-ERRSEV-OORD                PIC X.                    00132500
132600*                                                                 00132600
132700       15 FILLER                  REDEFINES CO-ERRSEV-OORD.       00132700
132800          20 CO-SEVERITE                PIC X.                    00132800
132900*                                                                 00132900
133000*----- 901 - 904 -----  CODE ERREUR                               00133000
133100       15 CO-ERROR-OORD                 PIC X(4).                 00133100
133200*                                                                 00133200
133300       15 FILLER                  REDEFINES CO-ERROR-OORD.        00133300
133400          20 ERR-CODE                   PIC X(4).                 00133400
133500*                                                                 00133500
133600       15 FILLER                  REDEFINES CO-ERROR-OORD.        00133600
133700          20 ERR-CODE-GDIFC             PIC X(4).                 00133700
133800*                                                                 00133800
133900*----- 905 - 924 -----  INFOS ERREUR                              00133900
134000       15 TE-ERROR-OORD                 PIC X(20).                00134000
134100*                                                                 00134100
134200*----- 925 - 956 -----  RAISON ERREUR                             00134200
134300       15 TE-CAUSE-OORD                 PIC X(32).                00134300
134400*                                                                 00134400
134500*----- 957 -1056 -----  COMMENTAIRE SUR ORDRE                     00134500
134600       15 TE-COMM-OORD                  PIC X(100).               00134600
134700*                                                                 00134700
134800       15 FILLER                  REDEFINES TE-COMM-OORD.         00134800
134900          20 TE-REF-GDIFC               PIC X(100).               00134900
135000*                                                                 00135000
135100*---- 1057       -----  RAISON ECHANGE                            00135100
135200       15 CO-EXCH-OORD                  PIC X.                    00135200
135300*                                                                 00135300
      *-----1058 -1061 -----                                            00135310
             15 NS-REFPO-074OORD              PIC 9(4).                 00135320
      *                                                                 00135330
      *-----1062 -1063 ----- CODE MULTI CHANNEL SIGNING                 00135340
             15 CO-POSTPON-074OORD            PIC X(2).                 00135341
      *                                                                 00135342
      *-----1064 -1089 ----- TIMESTAMP CUT OFF SIGNATURE                00135343
             15 TS-ENDVAL-074OORD             PIC X(26).                00135344
      *                                                                 00135350
135400*-----1090 -1098 -----                                            00135400
135500       15 FILLER                        PIC X(09).                00135500
135600*                                                                 00135600
135700*+++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++  00135700
135800*----          P R I N T                                 -----    00135800
135900*              ---------                                          00135900
136000*-----1099 -1101 -----  N° LIGNE DE PRINT                         00136000
136100       15 NS-PRINT-POKB                 PIC 9(3).                 00136100
136200*                                                                 00136200
136300*-----1102 -1104 -----  NB LIGNE DE PRINT                         00136300
136400       15 NB-PRINT-POKB                 PIC 9(3).                 00136400
136500*                                                                 00136500
136600*---- 1105 -1120 -----  RESERVE                                   00136600
136700       15 FILLER                        PIC X(16).                00136700
136800*                                                                 00136800
136900*+++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++  00136900
137000*----          E F I / R F E                             -----    00137000
137100*              -------------                                      00137100
137200*-----1121 -1123 -----  THEORETISCH PERCENTAGE EFI/RFE            00137200
137300       15 RA-RFE-OORD                  PIC S9(2)V9(2) COMP-3.     00137300
137400*                                                                 00137400
137500*-----1124 -1124 -----  SWITCH VRIJSTELLING EFI/RFE               00137500
137600       15 CO-RFE-OORD                  PIC X.                     00137600
137700*                                                                 00137700
137800*-----1125 -1132 -----  BEDRAG EFI/RFE                            00137800
137900       15 AM-RFE-OORD                  PIC S9(13)V9(2) COMP-3.    00137900
138000*                                                                 00138000
138100*-----1133 -1140 -----  AANKOOPDATUM                              00138100
138200       15 DA-BUY-OORD                  PIC X(8).                  00138200
138201*                                                                 00138201
138210*-----1141 -1148 -----  MONTANT DE BASE EFI/RFE                   00138210
138220       15 AM-BASERFE-OORD              PIC S9(13)V9(2) COMP-3.    00138220
138230*                                                                 00138230
138240*---- 1149 -1200 -----  RESERVE                                   00138240
138250       15 FILLER                        PIC X(52).                00138250
138290*                                                                 00138290
138700*+++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++  00138700
138800*----          C O M P T A                                 -----  00138800
138900*              -----------                                        00138900
139000*----- 1201 - 1500----                                            00139000
139100    10 INFO-COMPTA.                                               00139100
139200*                                                                 00139200
139300*----- 1201 - 1203 ----  UNITÉ DE TEMPS (QZ)                      00139300
139400       15 CO-TIUT-ISSUE                PIC X(03).                 00139400
139500*                                                                 00139500
139600       15 FILLER                  REDEFINES CO-TIUT-ISSUE.        00139600
139700          20 CO-TIUT-OPER              PIC X(03).                 00139700
139800*                                                                 00139800
139900*----- 1204 - 1209 ----                                           00139900
140000       15 NB-CMREP-ISSUE               PIC S9(2)V9(8) COMP-3.     00140000
140100*                                                                 00140100
140200*----- 1210 - 1217 ----                                           00140200
140300       15 DA-UE-INT                    PIC 9(8).                  00140300
140400       15 FILLER       REDEFINES DA-UE-INT.                       00140400
140500          20 DA-UE-INT-C               PIC 99.                    00140500
140600          20 DA-UE-INT-Y               PIC 99.                    00140600
140700          20 DA-UE-INT-M               PIC 99.                    00140700
140800          20 DA-UE-INT-D               PIC 99.                    00140800
140900       15 DA-UE-INT-X  REDEFINES DA-UE-INT.                       00140900
141000          20 DA-UE-INT-CY-X.                                      00141000
141100           25 DA-UE-INT-C-X            PIC XX.                    00141100
141200           25 DA-UE-INT-Y-X            PIC XX.                    00141200
141300          20 DA-UE-INT-M-X             PIC XX.                    00141300
141400          20 DA-UE-INT-D-X             PIC XX.                    00141400
141500       15 FILLER                  REDEFINES DA-UE-INT.            00141500
141600          20 DA-UE-INT-OPER            PIC X(8).                  00141600
141700       15 FILLER                  REDEFINES DA-UE-INT.            00141700
141800          20 DA-VVD-COUP               PIC X(8).                  00141800
141900*                                                                 00141900
142000       15 FILLER                  REDEFINES DA-UE-INT.            00142000
142100          20 DA-VVD-PAY                PIC X(8).                  00142100
142200*                                                                 00142200
142300*----- 1218 - 1337 ---- DATES ÉCHÉANCES                           00142300
142400       15 TAB-DA-ECHEANCE.                                        00142400
142500        20  FILLER                      OCCURS 15.                00142500
142600         25  DA-ECHEANCE               PIC 9(8).                  00142600
142700         25  DA-ECHEANCE-X   REDEFINES DA-ECHEANCE.               00142700
142800          30  DY-ECHEANCE              PIC 9(4).                  00142800
142900          30  DM-ECHEANCE              PIC 9(2).                  00142900
143000          30  DD-ECHEANCE              PIC 9(2).                  00143000
143100*                                                                 00143100
143200       15 TAB-DA-VVD-OPER REDEFINES TAB-DA-ECHEANCE.              00143200
143300          20 DA-VVD-OPER OCCURS 15 PIC X(8).                      00143300
143400*                                                                 00143400
143500*----- 1338 - 1339 ----  AANTAL EFFECTVERVALDAGEN                 00143500
143600       15 NB-ECHEANCE                  PIC 99.                    00143600
143700*                                                                 00143700
143800       15 FILLER REDEFINES NB-ECHEANCE.                           00143800
143900          20 NB-VVD-OPER               PIC 99.                    00143900
144000*                                                                 00144000
144100*----- 1340 - 1341 ----  VOLGNUMMER EFFECTVERVALDAG               00144100
144200       15 NO-ECHEANCE                  PIC 99.                    00144200
144300*                                                                 00144300
144400       15 FILLER REDEFINES NO-ECHEANCE.                           00144400
144500          20 NS-VVD-OPER               PIC 99.                    00144500
144600*                                                                 00144600
144700*----- 1342 - 1344 ---- THEORETISCH % ROERENDE VOORHEFFING        00144700
144800       15 RA-RV-FORM-AS                PIC S99V999 COMP-3.        00144800
144900*                                                                 00144900
145000       15 FILLER                  REDEFINES RA-RV-FORM-AS.        00145000
145100          20 RA-VHEF-OPER              PIC S99V999 COMP-3.        00145100
145200*                                                                 00145200
145300       15 FILLER                  REDEFINES RA-RV-FORM-AS.        00145300
145400          20 RA-RV-COUP                PIC S99V999 COMP-3.        00145400
145500*                                                                 00145500
145600       15 FILLER                  REDEFINES RA-RV-FORM-AS.        00145600
145700          20 RA-RV-PAY                 PIC S99V999 COMP-3.        00145700
145800*                                                                 00145800
145900*----- 1345 - 1345 ---- KODE BEURSTAKS                            00145900
146000       15 CO-TOB-FORM-AS               PIC X.                     00146000
146100*                                                                 00146100
146200       15 FILLER REDEFINES CO-TOB-FORM-AS.                        00146200
146300          20 CO-TOB-OPER               PIC X.                     00146300
146400*                                                                 00146400
146500*----- 1346 - 1346 ---- CODE TERUGBETALING                        00146500
146600       15 CO-REMB-COUP                 PIC X(01).                 00146600
146700*                                                                 00146700
146800       15 FILLER                  REDEFINES CO-REMB-COUP.         00146800
146900          20 CO-REMB-PAY               PIC X(01).                 00146900
147000*                                                                 00147000
147100*----- 1347 - 1347 ---- CODE TEST-REEEL (' '/'T'/'R')             00147100
147200       15 CO-TST-OPER                  PIC X(01).                 00147200
147300*                                                                 00147300
147400       15 FILLER                  REDEFINES CO-TST-OPER.          00147400
147500          20 CO-TST-COUP               PIC X(01).                 00147500
147600*                                                                 00147600
147700*----- 1348 - 1348 ----   CODE VERBLIJFHOUDER ('0', '1')          00147700
147800       15 CO-RESIDEN                   PIC X(01).                 00147800
147900                                                                  00147900
148000*----- 1349 - 1354 -----   CI OMLOOP EFFECT                       00148000
148100       15 NR-CI-OM-FORM-AS             PIC 9(06).                 00148100
148200*                                                                 00148200
148300*----- 1355 - 1356 ----   LANDCODE                                00148300
148400       15 CO-CNTR                      PIC X(02).                 00148400
148500*                                                                 00148500
148600*----- 1357 - 1364 ----   BONIFICATIEVOET                         00148600
148700       15 RA-BONIF                     PIC S9(03)V9(12) COMP-3.   00148700
                                                                        00148701
148600*----- 1365 - 1386 ----   RESERVE                                 00148710
148700       15 FILLER                       PIC X(22).                 00148720
      *                                                                 00148721
148600*----- 1387 - 1394 ----   DATUM VOOR PRE-CRE EN REGISTER          00148730
148700       15 DA-COMPTA-ORIG-OPER.                                    00148740
                20 DA-COMPTA-ORIG-OPER-Y     PIC XXXX.                  00148750
                20 DA-COMPTA-ORIG-OPER-M     PIC XX.                    00148760
                20 DA-COMPTA-ORIG-OPER-D     PIC XX.                    00148770
             15 FILLER REDEFINES DA-COMPTA-ORIG-OPER.                   00148780
               20 DA-COMPTA-ORIG-OPER-R      PIC X(8).                  00148790
148800*                                                                 00148800
148900*----- 1395 - 1400 ----   BOEKHOUDKUNDIG PRODUCTNUMMER            00148900
149000       15 NR-NRSEQ-060PROD             PIC X(6).                  00149000
149100*                                                                 00149100
149200*+++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++  00149200
149300*----          A A N V U L L I N G   V M B V               -----  00149300
149400*              -----------------------------                      00149400
149500*----- 1401 - 1500 ----                                           00149500
149600    10 INFO-VMBV.                                                 00149600
149700*                                                                 00149700
149800*----- 1401 - 1408 ---- BOEKINGSDATUM                             00149800
149900       15 DA-COMPTABILISATION-OPER      PIC X(8).                 00149900
150000*                                                                 00150000
150100*----- 1409 - 1410 ---- SITUATIECODE MANTEL/COUPON                00150100
150200       15 CO-SIT-OPER                   PIC XX.                   00150200
150300*                                                                 00150300
150400*----- 1411 - 1418 ---- BRUTOBEDRAG TUSSENTIJDSE INTREST (HM)     00150400
150500       15 AM-FIB-OPER                   PIC S9(13)V9(2) COMP-3.   00150500
150600*                                                                 00150600
150700*----- 1419 - 1426 ---- BRUTOBEDRAG TUSSENTIJDSE INTREST (DAGEN)  00150700
150800       15  SL-AM-DGFIB-OPER             PIC S9(13)V9(2) COMP-3.   00150800
150900*                                                                 00150900
151000*----- 1427 - 1434 ---- RV-BEDRAG OP TUSSENTIJDSE INTREST (HM)    00151000
151100       15 AM-WTI-FJ-OPER                PIC S9(13)V9(2) COMP-3.   00151100
151200*                                                                 00151200
151300*----- 1435 - 1442 ---- VOORAFBETAALDE INTREST // KAPITAAL        00151300
151400       15  AM-IACPA-OPER                PIC S9(13)V9(2) COMP-3.   00151400
151500*                                                                 00151500
151600*----- 1443 - 1450 --- BRUTO INTREST/MEERWAARDE/WAARDEVERMINDERING00151600
      *                           /BONIFICATIE                          00151610
151700*----- |||||||||||||||||||||||||||||||||||||||||||||||||||||||||||00151700
151800*----- OPGELET:                                                   00151800
151900*-----   IN VMBV ALTIJD >= 0, VERRICHTINGSCODE GEEFT POS/NEG      00151900
152000*-----   IN VMBA <=0 OF >=0 VOLGENS VERRICHTINGSCODE)             00152000
152100*----- |||||||||||||||||||||||||||||||||||||||||||||||||||||||||||00152100
152200       15 AM-BRUTO-OPER                 PIC S9(13)V9(2) COMP-3.   00152200
152300*                                                                 00152300
152400       15 FILLER                  REDEFINES AM-BRUTO-OPER.        00152400
152500          20 AM-INTB-OPER               PIC S9(13)V9(2) COMP-3.   00152500
152600*                                                                 00152600
152700       15 FILLER                  REDEFINES AM-BRUTO-OPER.        00152700
152800          20 AM-INTD-OPER               PIC S9(13)V9(2) COMP-3.   00152800
152900*                                                                 00152900
153000       15 FILLER                  REDEFINES AM-BRUTO-OPER.        00153000
153100          20 AM-PL-VALB-OPER            PIC S9(13)V9(2) COMP-3.   00153100
153200*                                                                 00153200
153300       15 FILLER                  REDEFINES AM-BRUTO-OPER.        00153300
153400          20 AM-BRUTO-PAY               PIC S9(13)V9(2) COMP-3.   00153400
153500*                                                                 00153500
153600*----- 1451 - 1458 --- NETTO INTREST/MEERWAARDE/WAARDEVERMINDERING00153600
      *                           /BONIFICATIE                          00153610
153700       15 AM-NETTO-OPER                 PIC S9(13)V9(2) COMP-3.   00153700
153800*                                                                 00153800
153900       15 FILLER                  REDEFINES AM-NETTO-OPER.        00153900
154000          20 AM-INTN-OPER               PIC S9(13)V9(2) COMP-3.   00154000
154100*                                                                 00154100
154200       15 FILLER                  REDEFINES AM-NETTO-OPER.        00154200
154300          20 AM-INTT-OPER               PIC S9(13)V9(2) COMP-3.   00154300
154400*                                                                 00154400
154500       15 FILLER                  REDEFINES AM-NETTO-OPER.        00154500
154600          20 AM-PL-VALN-OPER            PIC S9(13)V9(2) COMP-3.   00154600
154700*                                                                 00154700
154800*----- 1459 - 1466 --- RV OP INTREST/MEERWAARDE/BONIFICATIE       00154800
154900       15 AM-PREC-OPER                  PIC S9(13)V9(2) COMP-3.   00154900
155000*                                                                 00155000
155100*----- 1467 - 1474 --- NOMINAAL (+/- VOLGENS VERRICHTINGSCODE)    00155100
155200       15 AM-CNS-PAY                    PIC S9(13)V9(2) COMP-3.   00155200
155300*                                                                 00155300
155400*----- 1475 - 1477 --- RANG 1STE COUPON UITBETALING               00155400
155500       15 NS-RANK-MIN-PAY-R.                                      00155500
155600          20 NS-RANK-MIN-PAY            PIC 999.                  00155600
155700*                                                                 00155700
155800*----- 1478 - 1480 --- RANG LAATSTE COUPON UITBETALING            00155800
155900       15 NS-RANK-MAX-PAY-R.                                      00155900
156000          20 NS-RANK-MAX-PAY            PIC 999.                  00156000
156100*                                                                 00156100
156200*----- 1481 - 1488 --- COUPONVERVALDAG (1STE COUPON)              00156200
156300       15 DA-UEP-PAY.                                             00156300
156400          20 DA-UEP-PAY-Y.                                        00156400
156500             25 DA-UEP-PAY-Y1           PIC XX.                   00156500
156600             25 DA-UEP-PAY-Y2           PIC XX.                   00156600
156700          20 DA-UEP-PAY-M               PIC XX.                   00156700
156800          20 DA-UEP-PAY-D               PIC XX.                   00156800
156900       15 FILLER         REDEFINES DA-UEP-PAY.                    00156900
157000          20 DA-UEP-PAY-R               PIC 9(8).                 00157000
157100*                                                                 00157100
157200*----- 1489 - 1496 --- BLOKVERVALDAG (= VERVALDAG LAATSTE COUPON) 00157200
157300       15 DA-UEP-MAX-PAY.                                         00157300
157400          20 DA-UEP-MAX-PAY-Y.                                    00157400
157500             25 DA-UEP-MAX-PAY-Y1      PIC XX.                    00157500
157600             25 DA-UEP-MAX-PAY-Y2      PIC XX.                    00157600
157700          20 DA-UEP-MAX-PAY-M          PIC XX.                    00157700
157800          20 DA-UEP-MAX-PAY-D          PIC XX.                    00157800
157900       15 FILLER         REDEFINES DA-UEP-MAX-PAY.                00157900
158000          20 DA-UEP-MAX-PAY-R          PIC 9(8).                  00158000
158100*                                                                 00158100
158200*----- 1497 - 1500 --- RESERVE                                    00158200
158300       15 FILLER                        PIC X(4).                 00158300
