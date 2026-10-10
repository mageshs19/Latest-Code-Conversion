000100*                                                                 00000100
000200******************************************************************00000200
000300*                  -- VMBD205I --                                 00000300
000400*  DESCRIPTION : FICHIER DE BASE POUR LA CHAINE VMBD - CONTROLE   00000400
000500*                ET TRAITEMENT DES OPERATIONS BCI.                00000500
000600*                IL EST CREE DANS LE PROGRAMME VM1BD205           00000600
000700*                                         ET EST AFFINE EN        00000700
000800*                FONCTION DES DIFFERENTS CONTROLES ET TRAITEMENTS.00000800
000900*                                                                 00000900
001000*         --->   WIJZIGINGEN OOK AANBRENGEN IN VMBD510I || <---   00001000
001100*                                                                 00001100
001200*  LRECL       : 1200                                             00001200
001300*                (REPRIS DU VMBD205S ET REVU POUR L'EURO          00001300
001400*                     J-M BOOGAERTS  96/09)                       00001400
001500*                (2001/07 JM BOOGAERTS                            00001500
001600*                    AJOUT ZONES LECT.OPT. POUR TKB 10 ANS)       00001600
001700*                (REPRIS DU VMBD205X ET REVU POUR L'INTÉGRATION   00001700
001800*                     J-M BOOGAERTS  2003/03 )                    00001800
001900*                (QUELQUES MODIFICATIONS                          00001900
002000*                     PH VERSTRAETEN 2003/05 )                    00002000
002100*                (AANGEVULD OM OOK VMBVBCIX, VMBAMINX, VMBASLKX   00002100
002200*                 EN VMBAPAYX TE VERVANGEN                        00002200
002300*                     H.DE VELDER    2003/06 )                    00002300
002600*                AANGEVULD MET STATUS UITBETALING (CO-STREMB)     00002600
002700*                      '1' = UITBETALING OP EVVD                  00002700
002800*                      '2' = UITBETALING OP TVVD                  00002800
002801*                     THEUJ          2003/09)                     00002801
002810*                (AANGEVULD MET ZONES EFI/RFE                     00002810
002830*                     A.SÉCULIER     2004/11 )                    00002830
002900*             -  J-M BOOGAERTS 2007/04                            00002900
002910*                     AJOUT MT BASE RFE                           00002910
      *             -  IELEE 22/07/10 : P31 : PRJ 5680  POSITIEBEHEER   00002911
      *                 ADD NR-REFINT EN NS-REFPO                       00002912
      *             -  TERMA 24/04/12 : P39 : PRJ 131851 DI RUPO        00002913
      *                 ADD CO-TDR EN RA-TDR                            00002914
      *             -  IELEE 25/08/14 : P47 : PRJ 159770 FATCA          00002915
      *                 ADD CO-FATCA, CO-POSTPON, TS-ENDVAL             00002916
002920*                                                                 00002920
002930*                                                                 00002930
003000****************************************************************  00003000
003100*                                                                 00003100
003200*----- POS 001 - 1200 -----                                       00003200
003300 01  VMBD205I.                                                    00003300
003400*                                                                 00003400
003500*+++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++00003500
003600*                                                                 00003600
003700*+++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++00003700
003800*-----           I N F O   O P E R A T I O N                 -----00003800
003900*                ---------------------------                      00003900
004000*----- 001 - 200 -----                                            00004000
004100    10 INFO-OPERATION.                                            00004100
004200*                                                                 00004200
004300*----- 001 - 006 -----  CI OPERATION                              00004300
004400       15 NR-CIO-FORM-AS.                                         00004400
004500          20 NR-CIO-FORM-AS-R           PIC 9(6).                 00004500
004600*                                                                 00004600
004700       15 NR-CIO-MESS-RE          REDEFINES NR-CIO-FORM-AS.       00004700
004800          20 NR-CIO-MESS-RE-R           PIC 9(6).                 00004800
004900*                                                                 00004900
005000       15 NR-CIO-GDIFC-R          REDEFINES NR-CIO-FORM-AS.       00005000
005100          20 NR-CIO-GDIFC               PIC 9(6).                 00005100
005200*                                                                 00005200
005300       15 NR-CIO-OORD-X           REDEFINES NR-CIO-FORM-AS.       00005300
005400          20 NR-CIO-OORD                PIC 9(6).                 00005400
005500*                                                                 00005500
005600       15 NR-CIO-POKB-X           REDEFINES NR-CIO-FORM-AS.       00005600
005700          20 NR-CIO-POKB                PIC 9(6).                 00005700
005800*                                                                 00005800
005900       15 NR-CIO-OPER-X           REDEFINES NR-CIO-FORM-AS.       00005900
006000          20 NR-CIO-OPER                PIC 9(6).                 00006000
006100*                                                                 00006100
006200       15 NR-CIO-COUP-R           REDEFINES NR-CIO-FORM-AS.       00006200
006300          20 NR-CIO-COUP                PIC 9(6).                 00006300
006400*                                                                 00006400
006500       15 NR-CIO-PAY-R            REDEFINES NR-CIO-FORM-AS.       00006500
006600          20 NR-CIO-PAY                 PIC 9(6).                 00006600
006700*                                                                 00006700
006800*----- 007 - 012 -----  DI                                        00006800
006900       15 NR-ID-FORM-AS                 PIC 9(6).                 00006900
007000       15 NR-ID-FORM-AS-R         REDEFINES NR-ID-FORM-AS.        00007000
007100          20 NR-ID-FORM-AS-R1           PIC 9(5).                 00007100
007200          20 NR-ID-FORM-AS-R2           PIC 9.                    00007200
007300*                                                                 00007300
007400       15 NR-ID-MESS-RE           REDEFINES NR-ID-FORM-AS.        00007400
007500          20 NR-ID-MESS-RE-R            PIC 9(6).                 00007500
007600*                                                                 00007600
007700       15 NR-ID-GDIFC-R           REDEFINES NR-ID-FORM-AS.        00007700
007800          20 NR-ID-GDIFC                PIC 9(6).                 00007800
007900*                                                                 00007900
008000       15 NR-DI-OORD-X            REDEFINES NR-ID-FORM-AS.        00008000
008100          20 NR-DI-OORD                 PIC 9(6).                 00008100
008200*                                                                 00008200
008300       15 NR-DI-POKB-X            REDEFINES NR-ID-FORM-AS.        00008300
008400          20 NR-DI-POKB                 PIC 9(6).                 00008400
008500*                                                                 00008500
008600       15 NR-ID-OPER-X            REDEFINES NR-ID-FORM-AS.        00008600
008700          20 NR-ID-OPER                 PIC 9(6).                 00008700
008800*                                                                 00008800
008900       15 NR-ID-COUP-X            REDEFINES NR-ID-FORM-AS.        00008900
009000          20 NR-ID-COUP                 PIC 9(6).                 00009000
009100*                                                                 00009100
009200       15 NR-ID-PAY-X             REDEFINES NR-ID-FORM-AS.        00009200
009300          20 NR-ID-PAY                  PIC 9(6).                 00009300
009400*                                                                 00009400
009500*----- 013 - 020 -----  DATE CREATION DU DOCUMENT                 00009500
009600       15 DA-CREA-FORM-AS.                                        00009600
009700          20 DA-CR-FORM-AS-Y.                                     00009700
009800             25 DA-CR-FORM-AS-Y1        PIC XX.                   00009800
009900             25 DA-CR-FORM-AS-Y2        PIC XX.                   00009900
010000          20 DA-CR-FORM-AS-M            PIC XX.                   00010000
010100          20 DA-CR-FORM-AS-D            PIC XX.                   00010100
010200*                                                                 00010200
010300       15 FILLER                  REDEFINES DA-CREA-FORM-AS.      00010300
010400          20 DA-CREA-FORM-AS-R          PIC 9(8).                 00010400
010500*                                                                 00010500
010600       15 DA-CR-MESS-RE           REDEFINES DA-CREA-FORM-AS.      00010600
010700          20 DA-CR-MESS-RE-Y.                                     00010700
010800             25 DA-CR-MESS-RE-Y1        PIC XX.                   00010800
010900             25 DA-CR-MESS-RE-Y2        PIC XX.                   00010900
011000          20 DA-CR-MESS-RE-M            PIC XX.                   00011000
011100          20 DA-CR-MESS-RE-D            PIC XX.                   00011100
011200*                                                                 00011200
011300       15 FILLER                  REDEFINES DA-CREA-FORM-AS.      00011300
011400          20 DA-CR-MESS-RE-R            PIC 9(8).                 00011400
011500*                                                                 00011500
011600       15 DA-CR-GDIFC-R           REDEFINES DA-CREA-FORM-AS.      00011600
011700          20 DA-CR-GDIFC                PIC 9(8).                 00011700
011800*                                                                 00011800
011900       15 DA-CR-OORD-X            REDEFINES DA-CREA-FORM-AS.      00011900
012000          20 DA-CR-OORD                 PIC 9(8).                 00012000
012100*                                                                 00012100
012200       15 DA-CR-POKB-X            REDEFINES DA-CREA-FORM-AS.      00012200
012300          20 DA-CR-POKB                 PIC 9(8).                 00012300
012400*                                                                 00012400
012500       15 DA-CR-OPER-X            REDEFINES DA-CREA-FORM-AS.      00012500
012600          20 DA-CR-OPER                 PIC 9(8).                 00012600
012700*                                                                 00012700
012800       15 DA-CR-COUP-X            REDEFINES DA-CREA-FORM-AS.      00012800
012900          20 DA-CR-COUP                 PIC 9(8).                 00012900
013000*                                                                 00013000
013100       15 DA-CR-PAY-X             REDEFINES DA-CREA-FORM-AS.      00013100
013200          20 DA-CR-PAY                  PIC 9(8).                 00013200
013300*                                                                 00013300
013400*----- 021 - 024 -----  CODE OPERATION GENERAL / DETAIL           00013400
013500       15 CT-OP-FORM-AS.                                          00013500
013600          20 CT-OPG-FORM-AS             PIC XX.                   00013600
013700          20 CT-OPD-FORM-AS             PIC XX.                   00013700
013800*                                                                 00013800
013900       15 FILLER                  REDEFINES CT-OP-FORM-AS.        00013900
014000          20 CT-OP-FORM-AS-R            PIC 9(4).                 00014000
014100*                                                                 00014100
014200       15 FILLER                  REDEFINES CT-OP-FORM-AS.        00014200
014300          20 CT-OPG-FORM-AS-R           PIC 99.                   00014300
014400          20 CT-OPD-FORM-AS-R           PIC 99.                   00014400
014500*                                                                 00014500
014600       15 CT-OP-MESS-RE           REDEFINES CT-OP-FORM-AS.        00014600
014700          20 CT-OPG-MESS-RE             PIC XX.                   00014700
014800          20 CT-OPD-MESS-RE             PIC XX.                   00014800
014900*                                                                 00014900
015000       15 FILLER                  REDEFINES CT-OP-FORM-AS.        00015000
015100          20 CT-OP-MESS-RE-R            PIC 9(4).                 00015100
015200*                                                                 00015200
015300       15 FILLER                  REDEFINES CT-OP-FORM-AS.        00015300
015400          20 CT-OPG-MESS-RE-R           PIC 99.                   00015400
015500          20 CT-OPD-MESS-RE-R           PIC 99.                   00015500
015600*                                                                 00015600
015700       15 CT-OP-GDIFC             REDEFINES CT-OP-FORM-AS.        00015700
015800          20 CT-OPG-GDIFC               PIC 99.                   00015800
015900          20 CT-OPD-GDIFC               PIC 99.                   00015900
016000*                                                                 00016000
016100       15 CO-OP-OORD              REDEFINES CT-OP-FORM-AS.        00016100
016200          20 CO-OPG-OORD                PIC 99.                   00016200
016300          20 CO-OPD-OORD                PIC 99.                   00016300
016400*                                                                 00016400
016500       15 FILLER                  REDEFINES CT-OP-FORM-AS.        00016500
016600          20 CO-OPG-OORD-X              PIC XX.                   00016600
016700          20 CO-OPD-OORD-X              PIC XX.                   00016700
016800*                                                                 00016800
016900       15 CO-OP-POKB              REDEFINES CT-OP-FORM-AS.        00016900
017000          20 CO-OPG-POKB                PIC 99.                   00017000
017100          20 CO-OPD-POKB                PIC 99.                   00017100
017200*                                                                 00017200
017300       15 FILLER                  REDEFINES CT-OP-FORM-AS.        00017300
017400          20 FILLER                     PIC XX.                   00017400
017500          20 CT-OPD-COUP                PIC XX.                   00017500
017600*                                                                 00017600
017700       15 FILLER                  REDEFINES CT-OP-FORM-AS.        00017700
017800          20 CO-OPG-POKB-X              PIC XX.                   00017800
017900          20 CO-OPD-POKB-X              PIC XX.                   00017900
018000*                                                                 00018000
018100       15 FILLER                  REDEFINES CT-OP-FORM-AS.        00018100
018200          20 CT-OPG-OPER                PIC XX.                   00018200
018300          20 CT-OPD-OPER                PIC XX.                   00018300
018400*                                                                 00018400
018500       15 FILLER                  REDEFINES CT-OP-FORM-AS.        00018500
018600          20 FILLER                     PIC XX.                   00018600
018700          20 CT-OPD-PAY                 PIC XX.                   00018700
018800*                                                                 00018800
018900*----- 025 - 030 -----  CI POSTE DE TRAVAIL                       00018900
019000       15 NR-CIW-FORM-AS.                                         00019000
019100          20 NR-CIW-FORM-AS-R           PIC 9(6).                 00019100
019200*                                                                 00019200
019300       15 FILLER                  REDEFINES NR-CIW-FORM-AS.       00019300
019400          20 FIL-CIW                    PIC X(6).                 00019400
019500*                                                                 00019500
019600       15 FILLER                  REDEFINES NR-CIW-FORM-AS.       00019600
019700          20 NR-CIW-GDIFC               PIC 9(6).                 00019700
019800*                                                                 00019800
019900       15 NR-CIINPTR-OORD-X       REDEFINES NR-CIW-FORM-AS.       00019900
020000          20 NR-CIINPTR-OORD            PIC 9(6).                 00020000
020100*                                                                 00020100
020200       15 NR-CIINPTR-POKB-X       REDEFINES NR-CIW-FORM-AS.       00020200
020300          20 NR-CIINPTR-POKB            PIC 9(6).                 00020300
020400*                                                                 00020400
020500       15 NR-CIW-OPER-X           REDEFINES NR-CIW-FORM-AS.       00020500
020600          20 NR-CIW-OPER                PIC 9(6).                 00020600
020700*                                                                 00020700
020800       15 NR-CIW-COUP-X           REDEFINES NR-CIW-FORM-AS.       00020800
020900          20 NR-CIW-COUP                PIC 9(6).                 00020900
021000*                                                                 00021000
021100       15 NR-CIW-PAY-R            REDEFINES NR-CIW-FORM-AS.       00021100
021200          20 NR-CIW-PAY                 PIC 9(6).                 00021200
021300*                                                                 00021300
021400*----- 031 - 038 -----  N° POSTE DE TRAVAIL                       00021400
021500       15 NR-WKPOST-OORD-X.                                       00021500
021600          20 NR-WKPOST-OORD             PIC 9(8).                 00021600
021700*                                                                 00021700
021800       15 NR-WKPOST-POKB-X        REDEFINES NR-WKPOST-OORD-X.     00021800
021900          20 NR-WKPOST-POKB             PIC 9(8).                 00021900
022000*                                                                 00022000
022100*----- 039 - 054 -----  N° RÉFÉRENCE DE L'ORDRE                   00022100
022200       15 NR-REFORD-OORD                PIC X(16).                00022200
022300*                                                                 00022300
022400       15 FILLER                  REDEFINES NR-REFORD-OORD.       00022400
022500          20 NR-REFORD-POKB             PIC X(16).                00022500
022600*                                                                 00022600
022700*----- 055 - 057 -----  N° LIGNE DE L'ORDRE                       00022700
022800       15 NS-LINE-OORD                  PIC 9(3).                 00022800
022900*                                                                 00022900
023000       15 FILLER                  REDEFINES NS-LINE-OORD.         00023000
023100          20 NS-LINE-POKB               PIC 9(3).                 00023100
023200*                                                                 00023200
023300       15 FILLER                  REDEFINES NS-LINE-OORD.         00023300
023400          20 NS-LINE-GDIFC              PIC 9(3).                 00023400
023500*                                                                 00023500
023600       15 NS-SEGRP-FORM-AS-R      REDEFINES NS-LINE-OORD.         00023600
023700          20 NS-SEGRP-FORM-AS           PIC 9(3).                 00023700
023800*                                                                 00023800
023900       15 NS-SEGRP-OPER-R         REDEFINES NS-LINE-OORD.         00023900
024000          20 NS-SEGRP-OPER              PIC 9(3).                 00024000
024100*                                                                 00024100
024200       15 FILLER                  REDEFINES NS-LINE-OORD.         00024200
024300          20 NS-LINE-COUP               PIC 9(3).                 00024300
024400*                                                                 00024400
024500       15 FILLER                  REDEFINES NS-LINE-OORD.         00024500
024600          20 NS-LINE-PAY                PIC 9(3).                 00024600
024700*                                                                 00024700
024800*----- 058 - 060 -----  NB LIGNE DE L'ORDRE                       00024800
024900       15 NB-LINE-OORD                  PIC 9(3).                 00024900
025000*                                                                 00025000
025100       15 FILLER                  REDEFINES NB-LINE-OORD.         00025100
025200          20 NB-LINE-GDIFC              PIC 9(3).                 00025200
025300*                                                                 00025300
025400       15 NB-GROUP-FORM-AS-R      REDEFINES NB-LINE-OORD.         00025400
025500          20 NB-GROUP-FORM-AS           PIC 9(3).                 00025500
025600*                                                                 00025600
025700       15 FILLER                  REDEFINES NB-LINE-OORD.         00025700
025800          20 NB-GROUP-OPER              PIC 9(3).                 00025800
025900*                                                                 00025900
026000       15 FILLER                  REDEFINES NB-LINE-OORD.         00026000
026100          20 NB-LINE-COUP               PIC 9(3).                 00026100
026200*                                                                 00026200
026300       15 FILLER                  REDEFINES NB-LINE-OORD.         00026300
026400          20 NB-LINE-PAY                PIC 9(3).                 00026400
026500*                                                                 00026500
026600*----- 061 - 062 -----  TYPE OPERATION SECURITIES                 00026600
026700       15 CO-TYPOPER-OORD               PIC X(2).                 00026700
026800*                                                                 00026800
026900*----- 063 - 088 -----  TIMESTAMP CRÉATION ORDRE                  00026900
027000       15 TS-CREA-OORD                  PIC X(26).                00027000
027100*                                                                 00027100
027200*----- 089 - 094 -----  TYPE TRANSACTION                          00027200
027300       15 CO-TTRANSA-OORD               PIC X(6).                 00027300
027400*                                                                 00027400
027500*----- 095 - 107 -----  N° TRANSACTION                            00027500
027600       15 NR-TRANS-OORD                 PIC X(13).                00027600
027700*                                                                 00027700
027800       15 FILLER                  REDEFINES NR-TRANS-OORD.        00027800
027900          20 NR-TRANS-POKB              PIC X(13).                00027900
028000*                                                                 00028000
028100*----- 108 - 110 -----  DEVISE DE L'OPERATION                     00028100
028200       15 SL-CO-DEV-FORM-AS             PIC X(3).                 00028200
028300*                                                                 00028300
028400       15 FILLER                  REDEFINES SL-CO-DEV-FORM-AS.    00028400
028500          20 CO-DEV-OORD                PIC X(3).                 00028500
028600*                                                                 00028600
028700       15 FILLER                  REDEFINES SL-CO-DEV-FORM-AS.    00028700
028800          20 CO-DEV-POKB                PIC X(3).                 00028800
028900*                                                                 00028900
029000       15 FILLER                  REDEFINES SL-CO-DEV-FORM-AS.    00029000
029100          20 CO-DEV-GDIFC               PIC X(3).                 00029100
029200*                                                                 00029200
029300       15 FILLER                  REDEFINES SL-CO-DEV-FORM-AS.    00029300
029400          20 CO-DEV-COUP                PIC X(3).                 00029400
029500*                                                                 00029500
029600       15 FILLER                  REDEFINES SL-CO-DEV-FORM-AS.    00029600
029700          20 CO-CURR-COUP               PIC X(3).                 00029700
029800*                                                                 00029800
029900       15 FILLER                  REDEFINES SL-CO-DEV-FORM-AS.    00029900
030000          20 CO-CURRC-OPER              PIC X(3).                 00030000
030100*                                                                 00030100
030200       15 FILLER                  REDEFINES SL-CO-DEV-FORM-AS.    00030200
030300          20 CO-CURRC-PAY               PIC X(3).                 00030300
030400*                                                                 00030400
030500*----- 111 - 118 -----  DATE VALEUR DE L'OPERATION                00030500
030600       15 DA-VA-FORM-AS.                                          00030600
030700          20 DA-VA-FORM-AS-Y.                                     00030700
030800             25 DA-VA-FORM-AS-Y1        PIC XX.                   00030800
030900             25 DA-VA-FORM-AS-Y2        PIC XX.                   00030900
031000          20 DA-VA-FORM-AS-M            PIC XX.                   00031000
031100          20 DA-VA-FORM-AS-D            PIC XX.                   00031100
031200*                                                                 00031200
031300       15 FILLER                  REDEFINES DA-VA-FORM-AS.        00031300
031400          20 DA-VA-FORM-AS-R            PIC 9(8).                 00031400
031500*                                                                 00031500
031600       15 FILLER                  REDEFINES DA-VA-FORM-AS.        00031600
031700          20 DA-VA-OORD                 PIC 9(8).                 00031700
031800*                                                                 00031800
031900       15 FILLER                  REDEFINES DA-VA-FORM-AS.        00031900
032000          20 DA-VA-OPER                 PIC 9(8).                 00032000
032100*                                                                 00032100
032200       15 FILLER                  REDEFINES DA-VA-FORM-AS.        00032200
032300          20 DA-VA-COUP                 PIC 9(8).                 00032300
032400*                                                                 00032400
032500       15 FILLER                  REDEFINES DA-VA-FORM-AS.        00032500
032600          20 DA-VA-PAY                  PIC 9(8).                 00032600
032700*                                                                 00032700
032800*----- 119       -----  DATE VALEUR MODIFIEE PAR AGENT            00032800
032900       15 CO-VM-FORM-AS.                                          00032900
033000          20 CO-VM-OORD                 PIC X.                    00033000
033100*                                                                 00033100
033200*----- 120 - 127 -----  DATE EXÉCUTION ORDRE                      00033200
033300       15 DA-EXEC-OORD                  PIC 9(8).                 00033300
033400*                                                                 00033400
033500*----- 128 - 129 -----  CANAL DE DISTRIBUTION                     00033500
033600       15 CO-TYPKAN2-OORD               PIC X(2).                 00033600
033700*                                                                 00033700
033800*----- 130 - 137 -----  USERID DE L'ORDRE                         00033800
033900       15 NR-USER-GDIFC                 PIC X(8).                 00033900
034000*                                                                 00034000
034100       15 FILLER                  REDEFINES NR-USER-GDIFC.        00034100
034200          20 NR-USER-OORD               PIC X(8).                 00034200
034300*                                                                 00034300
034400*----- 138 - 145 -----  DATE VISITE MANUELLE                      00034400
034500       15 DA-BEZACTM-OORD               PIC 9(8).                 00034500
034600*                                                                 00034600
034700*----- 146 - 153 -----  USERID VISITE MANUELLE                    00034700
034800       15 NR-BEZUSEM-OORD               PIC X(8).                 00034800
034900*                                                                 00034900
035000*----- 154 - 169 -----  N° DOCUMENT MANUEL                        00035000
035100       15 NR-DOCUMM-OORD                PIC X(16).                00035100
035200*                                                                 00035200
035300*----- 170 - 172 -----  CODE BACK-OFFICE CONSULT-PROFILE          00035300
035400       15 CO-BACKOFF-OORD               PIC X(3).                 00035400
035500*                                                                 00035500
035600*----- 173 - 174 -----  ORDRE INTRODUCTION BANQUE                 00035600
035700       15 CO-BANK-OORD                  PIC X(2).                 00035700
035800*                                                                 00035800
035900       15 FILLER                  REDEFINES CO-BANK-OORD.         00035900
036000          20 CO-BANK-POKB               PIC X(2).                 00036000
036100*                                                                 00036100
036200*----- 175       -----  TYPE DE VENTE                             00036200
036300       15 CT-SL-FORM-AS                 PIC X.                    00036300
036400*                                                                 00036400
036500       15 FILLER                  REDEFINES CT-SL-FORM-AS.        00036500
036600          20 CO-SEL-OORD                PIC X.                    00036600
036700*                                                                 00036700
036800       15 FILLER                  REDEFINES CT-SL-FORM-AS.        00036800
036900          20 CO-TYPE-OPER               PIC X.                    00036900
037000*                                                                 00037000
037100*----- 176 - 179 -----  CHECK DIGIT                               00037100
037200       15 NR-CD-FORM-AS.                                          00037200
037300          20 NR-CD-FORM-AS-R            PIC 9(4).                 00037300
037400*                                                                 00037400
037500       15 NR-CD-OORD-X            REDEFINES NR-CD-FORM-AS.        00037500
037600          20 NR-CD-OORD                 PIC 9(4).                 00037600
037700*                                                                 00037700
037800       15 NR-CD-POKB-X            REDEFINES NR-CD-FORM-AS.        00037800
037900          20 NR-CD-POKB                 PIC 9(4).                 00037900
038000*                                                                 00038000
038100*----- 180       -----  TYPE ORDRE (R/O)                          00038100
038200       15 CT-LINE-TE                    PIC X.                    00038200
038300*                                                                 00038300
038400       15 FILLER                  REDEFINES CT-LINE-TE.           00038400
038500          20 CO-ORDER-OORD              PIC X.                    00038500
038600*                                                                 00038600
038700       15 FILLER                  REDEFINES CT-LINE-TE.           00038700
038800          20 CT-LINE-TE-OPER            PIC X.                    00038800
038900*                                                                 00038900
039000*----- 181 - 186 -----  CI ÉTOILE                                 00039000
039100       15 NR-CISTER-OORD-X.                                       00039100
039200          20 NR-CISTER-OORD             PIC 9(6).                 00039200
039300*                                                                 00039300
039400*----- 187 - 200 -----  RESERVE                                   00039400
039500       15 FILLER                        PIC X(14).                00039500
039600*                                                                 00039600
039700*+++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++00039700
039800*-----               E M M I S S I O N S                     -----00039800
039900*                    -------------------                          00039900
040000*----- 201 - 300 -----                                            00040000
040100    10 INFO-ISSUE.                                                00040100
040200*----- 201 - 204 -----  N° PRODUIT                                00040200
040300       15 SL-NR-PROD-FORM-AS.                                     00040300
040400         20 NR-ID-040SECU               PIC X(4).                 00040400
040500*                                                                 00040500
040600       15 FILLER REDEFINES SL-NR-PROD-FORM-AS.                    00040600
040700         20 NR-PROD-GDIFC               PIC X(4).                 00040700
040800*                                                                 00040800
040900       15 FILLER REDEFINES SL-NR-PROD-FORM-AS.                    00040900
041000         20 SL-NR-PROD-OPER             PIC X(4).                 00041000
041100*                                                                 00041100
041200       15 FILLER REDEFINES SL-NR-PROD-FORM-AS.                    00041200
041300         20 NR-PROD-COUP                PIC X(4).                 00041300
041400*                                                                 00041400
041500       15 FILLER REDEFINES SL-NR-PROD-FORM-AS.                    00041500
041600         20 NR-SLIK-PAY                 PIC X(4).                 00041600
041700*                                                                 00041700
041800*----- 205 - 208 -----  N° SEQ. COND. ÉMISSION                    00041800
041900       15 NS-SEQ-040IRMO                PIC 9(4).                 00041900
042000*                                                                 00042000
042100*----- 209 - 216 -----  DATE ENTREE EN JOUISSANCE                 00042100
042200       15 DA-UB-FORM-AS.                                          00042200
042300          20 DA-UB-FORM-AS-Y.                                     00042300
042400             25 DA-UB-FORM-AS-Y1        PIC XX.                   00042400
042500             25 DA-UB-FORM-AS-Y2        PIC XX.                   00042500
042600          20 DA-UB-FORM-AS-M            PIC XX.                   00042600
042700          20 DA-UB-FORM-AS-D            PIC XX.                   00042700
042800*                                                                 00042800
042900       15 FILLER                  REDEFINES DA-UB-FORM-AS.        00042900
043000          20 DA-UB-FORM-AS-R            PIC 9(8).                 00043000
043100*                                                                 00043100
043200       15 FILLER                  REDEFINES DA-UB-FORM-AS.        00043200
043300          20 DA-UBSEC-040ISSU           PIC 9(8).                 00043300
043400*                                                                 00043400
043500       15 FILLER                  REDEFINES DA-UB-FORM-AS.        00043500
043600          20 DA-UB-OPER                 PIC 9(8).                 00043600
043700*                                                                 00043700
043800       15 FILLER                  REDEFINES DA-UB-FORM-AS.        00043800
043900          20 DA-UB-ST-COUP              PIC 9(8).                 00043900
044000*                                                                 00044000
044100       15 FILLER                  REDEFINES DA-UB-FORM-AS.        00044100
044200          20 DA-UB-ST-PAY               PIC 9(8).                 00044200
044300*                                                                 00044300
044400*----- 217 - 224 -----  DATE ECHEANCE                             00044400
044500       15 DA-UE-FORM-AS.                                          00044500
044600          20 DA-UE-FORM-AS-Y.                                     00044600
044700             25 DA-UE-FORM-AS-Y1        PIC XX.                   00044700
044800             25 DA-UE-FORM-AS-Y2        PIC XX.                   00044800
044900          20 DA-UE-FORM-AS-M            PIC XX.                   00044900
045000          20 DA-UE-FORM-AS-D            PIC XX.                   00045000
045100*                                                                 00045100
045200       15 FILLER                  REDEFINES DA-UE-FORM-AS.        00045200
045300          20 DA-UE-FORM-AS-R            PIC 9(8).                 00045300
045400*                                                                 00045400
045500       15 FILLER                  REDEFINES DA-UE-FORM-AS.        00045500
045600          20 DA-UE-OPER                 PIC 9(8).                 00045600
045700*                                                                 00045700
045800       15 FILLER                  REDEFINES DA-UE-FORM-AS.        00045800
045900          20 DA-UE-ST-COUP              PIC 9(8).                 00045900
046000*                                                                 00046000
046100       15 FILLER                  REDEFINES DA-UE-FORM-AS.        00046100
046200          20 DA-UE-ST-PAY               PIC 9(8).                 00046200
046300*                                                                 00046300
046400*----- 225 - 227 -----  DUREE DE L'EMISSION                       00046400
046500       15 DU-ST-FORM-AS.                                          00046500
046600          20 DU-ST-FORM-AS-R            PIC 9(3).                 00046600
046700*                                                                 00046700
046800       15 FILLER REDEFINES DU-ST-FORM-AS.                         00046800
046900          20 DU-ST-OPER                 PIC 9(3).                 00046900
047000*                                                                 00047000
047100       15 FILLER REDEFINES DU-ST-FORM-AS.                         00047100
047200          20 DU-ST-COUP                 PIC 9(3).                 00047200
047300*                                                                 00047300
047400       15 FILLER REDEFINES DU-ST-FORM-AS.                         00047400
047500          20 DU-ST-PAY                  PIC 9(3).                 00047500
047600*                                                                 00047600
047700*----- 228 - 230 -----  PERIODICITE 1ER CP                        00047700
047800       15 NB-PERI1-FORM-AS              PIC 9(3).                 00047800
047900*                                                                 00047900
048000       15 FILLER                  REDEFINES NB-PERI1-FORM-AS.     00048000
048100          20 NB-PERI1-GDIFC             PIC 9(3).                 00048100
048200*                                                                 00048200
048300       15 FILLER                  REDEFINES NB-PERI1-FORM-AS.     00048300
048400          20 NB-PERI1-COUP              PIC 9(3).                 00048400
048500*                                                                 00048500
048600       15 FILLER                  REDEFINES NB-PERI1-FORM-AS.     00048600
048700          20 NB-PERI1-PAY               PIC 9(3).                 00048700
048800*                                                                 00048800
048900*----- 231 - 233 -----  PERIODICITE AUTRES CP                     00048900
049000       15 NB-PERIA-FORM-AS              PIC 9(3).                 00049000
049100*                                                                 00049100
049200       15 FILLER                  REDEFINES NB-PERIA-FORM-AS.     00049200
049300          20 NB-PERIA-GDIFC             PIC 9(3).                 00049300
049400*                                                                 00049400
049500       15 FILLER                  REDEFINES NB-PERIA-FORM-AS.     00049500
049600          20 CO-TIUTRA-OPER             PIC 9(3).                 00049600
049700*                                                                 00049700
049800       15 FILLER                  REDEFINES NB-PERIA-FORM-AS.     00049800
049900          20 NB-PERIA-COUP              PIC 9(3).                 00049900
050000*                                                                 00050000
050100       15 FILLER                  REDEFINES NB-PERIA-FORM-AS.     00050100
050200          20 NB-PERIA-PAY               PIC 9(3).                 00050200
050300*                                                                 00050300
050400*----- 234       -----  TYPE DE COUPON                            00050400
050500       15 CO-COUP-FORM-AS               PIC X.                    00050500
050600*                                                                 00050600
050700       15 FILLER                  REDEFINES CO-COUP-FORM-AS.      00050700
050800          20 CO-COUP-GDIFC              PIC X.                    00050800
050900*                                                                 00050900
051000       15 FILLER                  REDEFINES CO-COUP-FORM-AS.      00051000
051100          20 CO-COUP-COUP               PIC X.                    00051100
051200*                                                                 00051200
051300       15 FILLER                  REDEFINES CO-COUP-FORM-AS.      00051300
051400          20 CO-COUP-PAY                PIC X.                    00051400
051500*                                                                 00051500
051600*----- 235       -----  TYPE KAPITALISATIE                        00051600
051700       15 SL-CO-TYPE-CAPT               PIC X.                    00051700
051800*                                                                 00051800
051900       15 FILLER                  REDEFINES SL-CO-TYPE-CAPT.      00051900
052000          20 CO-TYPE-CAPT               PIC X.                    00052000
052100*                                                                 00052100
052200       15 FILLER                  REDEFINES SL-CO-TYPE-CAPT.      00052200
052300          20 CO-FPL-PAY                 PIC X.                    00052300
052400*                                                                 00052400
052500*----- 236 - 239 -----  TAUX DE BASE                              00052500
052600       15 RA-BASE-FORM-AS-R.                                      00052600
052700          20 RA-BASE-FORM-AS            PIC S9(3)V9(3) COMP-3.    00052700
052800*                                                                 00052800
052900       15 FILLER                  REDEFINES RA-BASE-FORM-AS-R.    00052900
053000          20 RA-BS-OPER                 PIC S9(3)V9(3) COMP-3.    00053000
053100*                                                                 00053100
053200*----- 240 - 243 -----  TAUX DE CAPITALISATION                    00053200
053300       15 RA-CP-FORM-AS-R.                                        00053300
053400          20 RA-CP-FORM-AS              PIC S9(3)V9(3) COMP-3.    00053400
053500*                                                                 00053500
053600       15 FILLER                  REDEFINES RA-CP-FORM-AS-R.      00053600
053700          20 RA-CP-OPER                 PIC S9(3)V9(3) COMP-3.    00053700
053800*                                                                 00053800
053900*----- 244 - 247 -----  TAUX DU RACHAT                            00053900
054000       15 RA-SUP-GDIFR-X.                                         00054000
054100           20 RA-SUP-GDIFR              PIC S9(3)V9(3) COMP-3.    00054100
054200*                                                                 00054200
054300       15  FILLER                 REDEFINES RA-SUP-GDIFR-X.       00054300
054400           20 RA-SUP-OORD               PIC S9(3)V9(3) COMP-3.    00054400
054500*                                                                 00054500
054600       15  FILLER                 REDEFINES RA-SUP-GDIFR-X.       00054600
054700           20 RA-SUP-GDIFR-OPER         PIC S9(3)V9(3) COMP-3.    00054700
054800*                                                                 00054800
054900*----- 248 - 251 -----  PRIME EMISSION                            00054900
055000       15 RA-PS-FORM-AS-R.                                        00055000
055100          20 RA-PS-FORM-AS              PIC S9(3)V9(3) COMP-3.    00055100
055200*                                                                 00055200
055300       15 FILLER                  REDEFINES RA-PS-FORM-AS-R.      00055300
055400          20 RA-PS-OPER                 PIC S9(3)V9(3) COMP-3.    00055400
055500*                                                                 00055500
055600*----- 252 - 255 -----  PRIME DE REMBOURSEMENT                    00055600
055700       15 RA-PR-FORM-AS-R.                                        00055700
055800          20 RA-PR-FORM-AS              PIC S9(3)V9(3) COMP-3.    00055800
055900*                                                                 00055900
056000*----- 256 - 259 -----  TAUX DU PUT                               00056000
056100       15 SL-RA-PUT-GDIFAR-X.                                     00056100
056200          20 SL-RA-PUT-GDIFAR           PIC S9(3)V9(3) COMP-3.    00056200
056300*                                                                 00056300
056400       15 FILLER                  REDEFINES SL-RA-PUT-GDIFAR-X.   00056400
056500          20 SL-RA-PUT-OPER             PIC S9(3)V9(3) COMP-3.    00056500
056600*                                                                 00056600
056700*----- 260 - 263 -----  TAUX DES INT. INTERCAL. / QZ              00056700
056800       15 SL-RA-QZTTI-FORM-AS-X.                                  00056800
056900          20 SL-RA-QZTTI-FORM-AS        PIC S9(3)V9(3) COMP-3.    00056900
057000*                                                                 00057000
057100*----- 264 - 267 -----  TAUX DES INT. INTERCAL. / J               00057100
057200       15 SL-RA-DGTTI-FORM-AS-X.                                  00057200
057300          20 SL-RA-DGTTI-FORM-AS        PIC S9(3)V9(3) COMP-3.    00057300
057400*                                                                 00057400
057500*----- 268       -----  EXONÉRATION PM SUR PRIME EMISSION         00057500
057600       15  SL-CO-RVUPR-GDIFAR           PIC X.                    00057600
057700*                                                                 00057700
057800       15  FILLER                 REDEFINES SL-CO-RVUPR-GDIFAR.   00057800
057900          20 CO-PRTI-OORD               PIC X.                    00057900
058000*                                                                 00058000
058100       15  FILLER                 REDEFINES SL-CO-RVUPR-GDIFAR.   00058100
058200          20 SL-CO-RVUPR-OPER           PIC X.                    00058200
058300*                                                                 00058300
058400*----- 269 - 272 -----  PM SUR PRIME EMISSION                     00058400
058500       15 SL-RA-RVUPR-GDIFAR-X.                                   00058500
058600          20 SL-RA-RVUPR-GDIFAR         PIC 99V99.                00058600
058700*                                                                 00058700
058800       15 FILLER                  REDEFINES SL-RA-RVUPR-GDIFAR-X. 00058800
058900          20 SL-RA-RVUPR-OPER           PIC 99V99.                00058900
059000*                                                                 00059000
059100*----- 273 - 276 -----  PM SUR PRIME REMBOURSEMENT                00059100
059200       15 SL-RA-RVTPR-GDIFAR-X.                                   00059200
059300          20 SL-RA-RVTPR-GDIFAR         PIC 99V99.                00059300
059400*                                                                 00059400
059500       15 FILLER                  REDEFINES SL-RA-RVTPR-GDIFAR-X. 00059500
059600          20 SL-RA-RVTPR-OPER           PIC 99V99.                00059600
059700*                                                                 00059700
059800*----- 277 - 287 -----  N° INTERNE VMSU                           00059800
059900       15 NM-ID-010ISSU                 PIC X(11).                00059900
060000*                                                                 00060000
060100*----- 288       -----  TYPE EMISSION INTRODUIT                   00060100
060200       15 CO-ISSUIN-OORD                PIC X.                    00060200
060300*                                                                 00060300
060400*----- 289 - 297 -----  N° SVM                                    00060400
060500       15 NR-ISSUIN-OORD                PIC X(9).                 00060500
060600*                                                                 00060600
060700*----- 298 - 300 -----  RESERVE                                   00060700
060800       15 FILLER                        PIC X(3).                 00060800
060900*                                                                 00060900
061000*+++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++00061000
061100*-----      T I T R E S / D O S S I E R   T I T R E S        -----00061100
061200*           -----------------------------------------             00061200
061300*----- 301 - 380 -----                                            00061300
061400    10 INFO-TITRE.                                                00061400
061500*----- 301 - 313 -----  NO DU TITRE                               00061500
061600       15 NR-ST-FORM-AS                PIC 9(13).                 00061600
061700*                                                                 00061700
061800       15 NR-ST-FORM-AS-R         REDEFINES NR-ST-FORM-AS.        00061800
061900          20 NR-ST-FORM-AS-R1.                                    00061900
062000             25 NR-ST-FORM-AS-P1       PIC 99.                    00062000
062100             25 NR-ST-FORM-AS-P2       PIC 9(3).                  00062100
062200             25 FILLER            REDEFINES NR-ST-FORM-AS-P2.     00062200
062300                30 CT-ID-GOOD-R1       PIC 9.                     00062300
062400                30 CT-DN-GOOD-R1       PIC 9.                     00062400
062500                30 CO-LA-GOOD-R1       PIC 9.                     00062500
062600             25 NR-ST-FORM-AS-P3       PIC 9(7).                  00062600
062700          20 FILLER               REDEFINES NR-ST-FORM-AS-R1.     00062700
062800             25 NR-ST-FORM-AS-R2       PIC 9(12).                 00062800
062900          20 NR-ST-FORM-AS-P4          PIC 9.                     00062900
063000*                                                                 00063000
063100       15 FILLER                  REDEFINES NR-ST-FORM-AS.        00063100
063200          20 NR-ST-MESS-RE             PIC 9(13).                 00063200
063300*                                                                 00063300
063400       15 NR-ST-MESS-RE-R         REDEFINES NR-ST-FORM-AS.        00063400
063500          20 NR-ST-MESS-RE-RD1.                                   00063500
063600             25 NR-ST-MESS-RE-R1           PIC 99.                00063600
063700             25 NR-ST-MESS-RE-R2           PIC 9(3).              00063700
063800             25 NR-ST-MESS-RE-R3        PIC 9(7).                 00063800
063900          20 FILLER               REDEFINES NR-ST-MESS-RE-RD1.    00063900
064000             25 NR-ST-MESS-RE-RD2       PIC 9(12).                00064000
064100          20 NR-ST-MESS-RE-R4           PIC 9.                    00064100
064200*                                                                 00064200
064300       15 FILLER                  REDEFINES NR-ST-FORM-AS.        00064300
064400          20 NR-ST-GDIFC               PIC 9(13).                 00064400
064500*                                                                 00064500
064600       15 NR-ST-OORD-X            REDEFINES NR-ST-FORM-AS.        00064600
064700          20 NR-ST-OORD                PIC 9(13).                 00064700
064800*                                                                 00064800
064900       15 NR-ST-POKB-X            REDEFINES NR-ST-FORM-AS.        00064900
065000          20 NR-ST-POKB                PIC 9(13).                 00065000
065100*                                                                 00065100
065200       15 NR-ST-OPER-X            REDEFINES NR-ST-FORM-AS.        00065200
065300          20 NR-ST-OPER                PIC 9(13).                 00065300
065400*                                                                 00065400
065500       15 NR-ST-COUP-X            REDEFINES NR-ST-FORM-AS.        00065500
065600          20 NR-ST-COUP                PIC 9(13).                 00065600
065700*                                                                 00065700
065800       15 NR-ST-PAY-X             REDEFINES NR-ST-FORM-AS.        00065800
065900          20 NR-ST-PAY                 PIC 9(13).                 00065900
066000*                                                                 00066000
066100*----- 314 - 315 -----  NO DE SEQUENCE DU TITRE                   00066100
066200       15 NS-DB-STOCK-FORM-AS.                                    00066200
066300          20 NS-DB-STOCK-FORM-AS-R      PIC 99.                   00066300
066400*                                                                 00066400
066500       15 FILLER                  REDEFINES NS-DB-STOCK-FORM-AS.  00066500
066600          20 NS-DB-GDIFC                PIC 99.                   00066600
066700*                                                                 00066700
066800       15 FILLER                  REDEFINES NS-DB-STOCK-FORM-AS.  00066800
066900          20 NS-DBST-OORD               PIC 99.                   00066900
067000*                                                                 00067000
067100*----- 316 - 318 -----  NOMBRE DE PAPIER                          00067100
067200       15 NB-ST-MESS-RE.                                          00067200
067300          20 NB-ST-MESS-RE-R            PIC 9(3).                 00067300
067400*                                                                 00067400
067500       15 FILLER                  REDEFINES NB-ST-MESS-RE.        00067500
067600          20 NB-ST-OORD                 PIC 9(3).                 00067600
067700       15 FILLER                  REDEFINES NB-ST-MESS-RE.        00067700
067800          20 NB-JOURS                   PIC 9(3).                 00067800
067900*PV                                                               00067900
068000*                                                                 00068000
068100*----- 319 - 330 -----  NO DOSSIER TITRE                          00068100
068200       15 NR-DS-FORM-AS                 PIC 9(12).                00068200
068300*                                                                 00068300
068400       15 NR-DS-FORM-AS-R         REDEFINES NR-DS-FORM-AS.        00068400
068500          20 NR-DS-FORM-AS-P1           PIC 9(3).                 00068500
068600          20 NR-DS-FORM-AS-P2           PIC 9(7).                 00068600
068700          20 NR-DS-FORM-AS-P3           PIC 9(2).                 00068700
068800*                                                                 00068800
068900       15 NR-SECUR-OORD-X         REDEFINES NR-DS-FORM-AS.        00068900
069000          20 NR-SECUR-OORD              PIC 9(12).                00069000
069100*                                                                 00069100
069200       15 NR-DS-OPER-X            REDEFINES NR-DS-FORM-AS.        00069200
069300          20 NR-DS-OPER                 PIC 9(12).                00069300
069400*                                                                 00069400
069500       15 NR-DS-COUP-X            REDEFINES NR-DS-FORM-AS.        00069500
069600          20 NR-DS-COUP                 PIC 9(12).                00069600
069700*                                                                 00069700
069800       15 NR-DS-PAY-X             REDEFINES NR-DS-FORM-AS.        00069800
069900          20 NR-DS-PAY                  PIC 9(12).                00069900
070000*                                                                 00070000
070100*----- 331 - 342 -----  NO PORTEFEUILLE PORTEUR                   00070100
070200       15 NR-TOOND-OORD-X.                                        00070200
070300          20 NR-TOOND-OORD              PIC 9(12).                00070300
070400*                                                                 00070400
070500*----- 343 - 345 -----  1ER COUPON ATTACHE                        00070500
070600       15 NS-IDCP-FORM-AS-RED.                                    00070600
070700          20 NS-IDCP-FORM-AS            PIC 9(3).                 00070700
070800*                                                                 00070800
070900       15 FILLER                  REDEFINES NS-IDCP-FORM-AS-RED.  00070900
071000          20 NS-RANK-GDIFC              PIC 9(3).                 00071000
071100*                                                                 00071100
071200       15 FILLER                  REDEFINES NS-IDCP-FORM-AS-RED.  00071200
071300          20 NS-IDCP-OORD               PIC 9(3).                 00071300
071400*                                                                 00071400
071500       15 FILLER                  REDEFINES NS-IDCP-FORM-AS-RED.  00071500
071600          20 NS-IDCP-POKB               PIC 9(3).                 00071600
071700*                                                                 00071700
071800       15 FILLER                  REDEFINES NS-IDCP-FORM-AS-RED.  00071800
071900          20 NR-PREMCOUP-OPER           PIC 9(3).                 00071900
072000*                                                                 00072000
072100       15 FILLER                  REDEFINES NS-IDCP-FORM-AS-RED.  00072100
072200          20 NS-RANK-COUP               PIC 9(3).                 00072200
072300*                                                                 00072300
072400*----- 346 - 348 -----  DERNIER COUPON PAYE                       00072400
072500       15 NX-CPFDU-STOCK                PIC 9(3).                 00072500
072600       15 NX-CPAID-STOCK REDEFINES NX-CPFDU-STOCK                 00072600
072700                                        PIC 9(3).                 00072700
072800*                                                                 00072800
072900       15 FILLER                  REDEFINES NX-CPFDU-STOCK.       00072900
073000          20 NS-CPAID-OORD              PIC 9(3).                 00073000
073100*                                                                 00073100
073200*----- 349 - 351 -----  NB DE COUPON DANS LE BLOC                 00073200
073300       15 NB-CPSEQ-GDIFC                PIC 9(3).                 00073300
073400*                                                                 00073400
073500       15 FILLER                  REDEFINES NB-CPSEQ-GDIFC.       00073500
073600          20 NB-CPSEQ-OORD              PIC 9(3).                 00073600
073700*                                                                 00073700
073800       15 FILLER                  REDEFINES NB-CPSEQ-GDIFC.       00073800
073900          20 NB-CPSEQ-COUP              PIC 9(3).                 00073900
074000*                                                                 00074000
074100       15 FILLER                  REDEFINES NB-CPSEQ-GDIFC.       00074100
074200          20 NB-CPSEQ-PAY               PIC 9(3).                 00074200
074300*                                                                 00074300
074400*----- 352 - 355 -----  CD DERNIER COUPON DU BLOC                 00074400
074500       15 NR-CDAG-GDIFC                 PIC 9(4).                 00074500
074600*                                                                 00074600
074700       15 NR-CDAG-OORD-X          REDEFINES NR-CDAG-GDIFC.        00074700
074800          20 NR-CDAG-OORD               PIC 9(4).                 00074800
074900*                                                                 00074900
075000*----- 356       -----  REGIME LINGUISTIQUE                       00075000
075100       15 CO-LA-FORM-AS                 PIC X.                    00075100
075200*                                                                 00075200
075300       15 FILLER                  REDEFINES CO-LA-FORM-AS.        00075300
075400          20 CO-LA-OORD                 PIC X.                    00075400
075500*                                                                 00075500
075600       15 FILLER                  REDEFINES CO-LA-FORM-AS.        00075600
075700          20 CO-LA-POKB                 PIC X.                    00075700
075800*                                                                 00075800
075900*----- 357       -----  CODE CAPITALISATION                       00075900
076000       15 CO-CP-FORM-AS                 PIC X.                    00076000
076100*                                                                 00076100
076200       15 FILLER                  REDEFINES CO-CP-FORM-AS.        00076200
076300          20 CO-CP-OORD                 PIC X.                    00076300
076400*                                                                 00076400
076500*----- 358       -----  TYPE NO TITRE INTRODUIT                   00076500
076600       15 CO-STIN-OORD                  PIC X(1).                 00076600
076700*                                                                 00076700
076800*----- 359 - 372 -----  NO TITRE INTRODUIT                        00076800
076900       15 NR-STIN-OORD                  PIC X(14).                00076900
077000*                                                                 00077000
077100*----- 373 - 380 -----  RESERVE                                   00077100
077200       15 FILLER                        PIC X(8).                 00077200
077300*                                                                 00077300
077400*+++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++00077400
077500*-----      M O N T A N T S                                  -----00077500
077600*           ---------------                                       00077600
077700*----- 381 - 510 -----                                            00077700
077800    10 INFO-MT.                                                   00077800
077900*                                                                 00077900
078000*----- 381 - 388 -----  NOMINAL                                   00078000
078100       15 AM-CNS-FORM-AS-R.                                       00078100
078200          20 AM-CNS-FORM-AS             PIC S9(13)V9(2) COMP-3.   00078200
078300*                                                                 00078300
078400       15 FILLER                  REDEFINES AM-CNS-FORM-AS-R.     00078400
078500          20 AM-CNS-OORD                PIC S9(13)V9(2) COMP-3.   00078500
078600*                                                                 00078600
078700       15 FILLER                  REDEFINES AM-CNS-FORM-AS-R.     00078700
078800          20 AM-CNS-POKB                PIC S9(13)V9(2) COMP-3.   00078800
078900*                                                                 00078900
079000       15 FILLER                  REDEFINES AM-CNS-FORM-AS-R.     00079000
079100          20 AM-CND-GDIFC               PIC S9(13)V9(2) COMP-3.   00079100
079200*                                                                 00079200
079300       15 FILLER                  REDEFINES AM-CNS-FORM-AS-R.     00079300
079400          20 AM-CNS-OPER                PIC S9(13)V9(2) COMP-3.   00079400
079500*                                                                 00079500
079600       15 FILLER                  REDEFINES AM-CNS-FORM-AS-R.     00079600
079700          20 AM-CND-COUP                PIC S9(13)V9(2) COMP-3.   00079700
079800*                                                                 00079800
079900       15 FILLER                  REDEFINES AM-CNS-FORM-AS-R.     00079900
080000          20 AM-CNS-COUP                PIC S9(13)V9(2) COMP-3.   00080000
080100*                                                                 00080100
080200*----- 389 - 396 -----  MONTANT DE LA PRIME D'EMISSION            00080200
080300       15 AM-PS-FORM-AS-R.                                        00080300
080400          20 AM-PS-FORM-AS              PIC S9(13)V9(2) COMP-3.   00080400
080500*                                                                 00080500
080600       15 FILLER                  REDEFINES AM-PS-FORM-AS-R.      00080600
080700          20 AM-PS-OORD                 PIC S9(13)V9(2) COMP-3.   00080700
080800*                                                                 00080800
080900       15 FILLER                  REDEFINES AM-PS-FORM-AS-R.      00080900
081000          20 AM-PS-OPER                 PIC S9(13)V9(2) COMP-3.   00081000
081100*                                                                 00081100
081200       15 FILLER                  REDEFINES AM-PS-FORM-AS-R.      00081200
081300          20 AM-PSB-OPER                PIC S9(13)V9(2) COMP-3.   00081300
081400*                                                                 00081400
081500*----- 397 - 404 -----  REMBOURSABLE BRUT                         00081500
081600       15 AM-CND-FORM-AS-R.                                       00081600
081700          20 AM-CND-FORM-AS             PIC S9(13)V9(2) COMP-3.   00081700
081800*                                                                 00081800
081900       15 FILLER                  REDEFINES AM-CND-FORM-AS-R.     00081900
082000          20 AM-CND-OORD                PIC S9(13)V9(2) COMP-3.   00082000
082100*                                                                 00082100
082200       15 FILLER                  REDEFINES AM-CND-FORM-AS-R.     00082200
082300          20 AM-CND-OPER                PIC S9(13)V9(2) COMP-3.   00082300
082400*                                                                 00082400
082500*----- 405 - 412 -----  REMBOURSABLE NET                          00082500
082600       15 AM-CNDN-FORM-AS-R.                                      00082600
082700          20 AM-CNDN-FORM-AS            PIC S9(13)V9(2) COMP-3.   00082700
082800*                                                                 00082800
082900       15 FILLER                  REDEFINES AM-CNDN-FORM-AS-R.    00082900
083000          20 AM-CNDN-OORD               PIC S9(13)V9(2) COMP-3.   00083000
083100*                                                                 00083100
083200*----- 413 - 420 -----  MT INTERETS DES COUPONS                   00083200
083300       15 AM-INTER-FORM-AS-R.                                     00083300
083400          20 AM-INTER-FORM-AS           PIC S9(13)V9(2) COMP-3.   00083400
083500*                                                                 00083500
083600       15 FILLER                  REDEFINES AM-INTER-FORM-AS-R.   00083600
083700          20 AM-INTER-OORD              PIC S9(13)V9(2) COMP-3.   00083700
083800*                                                                 00083800
083900       15 FILLER                  REDEFINES AM-INTER-FORM-AS-R.   00083900
084000          20 AM-INTGR-GDIFC             PIC S9(13)V9(2) COMP-3.   00084000
084100*                                                                 00084100
084200       15 FILLER                  REDEFINES AM-INTER-FORM-AS-R.   00084200
084300          20 AM-INTGR-COUP              PIC S9(13)V9(2) COMP-3.   00084300
084400*                                                                 00084400
084500*----- 421 - 428 -----  MONTANT DES COUTS LORS DU PUT             00084500
084600       15 SL-AM-PUT-GDIFAR-X.                                     00084600
084700          20 SL-AM-PUT-GDIFAR           PIC S9(13)V9(2) COMP-3.   00084700
084800*                                                                 00084800
084900       15 FILLER                  REDEFINES SL-AM-PUT-GDIFAR-X.   00084900
085000          20 AM-PUT-OORD                PIC S9(13)V9(2) COMP-3.   00085000
085100*                                                                 00085100
085200       15 FILLER                  REDEFINES SL-AM-PUT-GDIFAR-X.   00085200
085300          20 SL-AM-PUT-OPER             PIC S9(13)V9(2) COMP-3.   00085300
085400*                                                                 00085400
085500*----- 429 - 436 -----  PRIME DE REMBOURSEMENT                    00085500
085600       15 SL-AM-TPREM-GDIFAR-X.                                   00085600
085700          20 SL-AM-TPREM-GDIFAR         PIC S9(13)V9(2) COMP-3.   00085700
085800*                                                                 00085800
085900       15 FILLER                  REDEFINES SL-AM-TPREM-GDIFAR-X. 00085900
086000          20 AM-TPREM-OORD              PIC S9(13)V9(2) COMP-3.   00086000
086100*                                                                 00086100
086200       15 FILLER                  REDEFINES SL-AM-TPREM-GDIFAR-X. 00086200
086300          20 SL-AM-TPREM-OPER           PIC S9(13)V9(2) COMP-3.   00086300
086400*                                                                 00086400
086500*----- 437 - 444 -----  PRIME DE SOUSCRIPTION                     00086500
086600       15 SL-AM-UPREM-GDIFAR-X.                                   00086600
086700          20 SL-AM-UPREM-GDIFAR         PIC S9(13)V9(2) COMP-3.   00086700
086800*                                                                 00086800
086900       15 FILLER                  REDEFINES SL-AM-UPREM-GDIFAR-X. 00086900
087000          20 AM-UPREM-OORD              PIC S9(13)V9(2) COMP-3.   00087000
087100*                                                                 00087100
087200       15 FILLER                  REDEFINES SL-AM-UPREM-GDIFAR-X. 00087200
087300          20 SL-AM-UPREM-OPER           PIC S9(13)V9(2) COMP-3.   00087300
087400*                                                                 00087400
087500*----- 445 - 452 -----  INTÉRÊTS BRUT DU BLOC DE COUPON           00087500
087600       15 AM-INB-GDIFC                  PIC S9(13)V9(2) COMP-3.   00087600
087700*                                                                 00087700
087800       15 FILLER                  REDEFINES AM-INB-GDIFC.         00087800
087900          20 AM-INB-OORD                PIC S9(13)V9(2) COMP-3.   00087900
088000                                                                  00088000
088100*                                                                 00088100
088200*----- 453 - 460 -----  INTÉRÊTS CAP DU BLOC DE COUPON            00088200
088300       15 AM-INBCA-GDIFC                PIC S9(13)V9(2) COMP-3.   00088300
088400*                                                                 00088400
088500       15 FILLER                  REDEFINES AM-INBCA-GDIFC.       00088500
088600          20 AM-INBCA-OORD              PIC S9(13)V9(2) COMP-3.   00088600
088700*                                                                 00088700
088800       15 FILLER                  REDEFINES AM-INBCA-GDIFC.       00088800
088900          20 AM-INBCA-COUP              PIC S9(13)V9(2) COMP-3.   00088900
089000*                                                                 00089000
089100*----- 461 - 468 -----  MONTANT NET DE L'OPERATION                00089100
089200       15 AM-CNSN-FORM-AS-R.                                      00089200
089300          20 AM-CNSN-FORM-AS            PIC S9(13)V9(2) COMP-3.   00089300
089400*            ( REDEFINITION POUR REMBOURSEMENT ET RACHAT )        00089400
089500       15 FILLER  REDEFINES AM-CNSN-FORM-AS-R.                    00089500
089600          20 AM-CRN-FORM-AS             PIC S9(13)V9(2) COMP-3.   00089600
089700*                                                                 00089700
089800       15 FILLER  REDEFINES AM-CNSN-FORM-AS-R.                    00089800
089900          20 AM-CNSN-OORD               PIC S9(13)V9(2) COMP-3.   00089900
090000*                                                                 00090000
090100       15 FILLER  REDEFINES AM-CNSN-FORM-AS-R.                    00090100
090200          20 AM-CNSN-OPER               PIC S9(13)V9(2) COMP-3.   00090200
090300*                                                                 00090300
090400*----- 469 - 476 -----  MONTANT NET DE LA TRANSACTION             00090400
090500       15 AM-CNSNTRN-OORD               PIC S9(13)V9(2) COMP-3.   00090500
090600*                                                                 00090600
090700       15 FILLER                  REDEFINES AM-CNSNTRN-OORD.      00090700
090800          20 AM-INNET-GDIFC             PIC S9(13)V9(2) COMP-3.   00090800
090900*                                                                 00090900
091000*----- 477 - 484 -----  TOTAL NOMINAL DE LA TRANSACTION           00091000
091100       15 AM-CNSTRAN-OORD               PIC S9(13)V9(2) COMP-3.   00091100
091200*                                                                 00091200
091300       15 AM-CNSSP-FORM-AS-RED    REDEFINES AM-CNSTRAN-OORD.      00091300
091400          20 AM-CNSSP-FORM-AS           PIC S9(13)V9(2) COMP-3.   00091400
091500*                                                                 00091500
091600*----- 485 - 492 -----  TOTAL BRUT DE LA TRANSACTION              00091600
091700       15 AM-CNSBTRN-OORD               PIC S9(13)V9(2) COMP-3.   00091700
091800*                                                                 00091800
091900       15 FILLER                  REDEFINES AM-CNSBTRN-OORD.      00091900
092000          20 AM-INGRT-FORM-AS           PIC S9(13)V9(2) COMP-3.   00092000
092100*                                                                 00092100
092200*                                                                 00092200
092300*----- 493 - 510 -----  RESERVE                                   00092300
092400       15 FILLER                        PIC X(18).                00092400
092500*                                                                 00092500
092600*+++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++00092600
092700*-----      T T I                                            -----00092700
092800*           -----                                                 00092800
092900*----- 511 - 550 -----                                            00092900
093000    10 INFO-TTI.                                                  00093000
093100*----- 511 - 518 -----  MONTANT DES QZ INTERCAL.                  00093100
093200       15 AM-FIN-FORM-AS-R.                                       00093200
093300          20 AM-FIN-FORM-AS             PIC S9(13)V9(2) COMP-3.   00093300
093400*                                                                 00093400
093500       15 FILLER                  REDEFINES AM-FIN-FORM-AS-R.     00093500
093600          20 AM-FIN-OORD                PIC S9(13)V9(2) COMP-3.   00093600
093700*                                                                 00093700
093800       15 FILLER                  REDEFINES AM-FIN-FORM-AS-R.     00093800
093900          20 AM-FIN-OPER                PIC S9(13)V9(2) COMP-3.   00093900
094000*                                                                 00094000
094100*----- 519 - 521 -----  NB DE QUINZAINES INTERCALAIRES            00094100
094200       15 NB-FI-FORM-AS-R.                                        00094200
094300          20 NB-FI-FORM-AS              PIC 999.                  00094300
094400*                                                                 00094400
094500       15 FILLER                  REDEFINES NB-FI-FORM-AS-R.      00094500
094600          20 NB-FI-OORD                 PIC 999.                  00094600
094700*                                                                 00094700
094800       15 FILLER                  REDEFINES NB-FI-FORM-AS-R.      00094800
094900          20 NB-FI-OPER                 PIC 999.                  00094900
095000*                                                                 00095000
095100*----- 522 - 529 -----  MT DES INT. INTERC. JOURN.                00095100
095200       15 SL-AM-DGTTI-FORM-AS-X.                                  00095200
095300          20 SL-AM-DGTTI-FORM-AS        PIC S9(13)V9(2) COMP-3.   00095300
095400*                                                                 00095400
095500       15 FILLER                  REDEFINES SL-AM-DGTTI-FORM-AS-X.00095500
095600          20 AM-DGTTI-OORD              PIC S9(13)V9(2) COMP-3.   00095600
095700*                                                                 00095700
095800       15 FILLER                  REDEFINES SL-AM-DGTTI-FORM-AS-X.00095800
095900          20 SL-AM-DGTTI-OPER           PIC S9(13)V9(2) COMP-3.   00095900
096000*                                                                 00096000
096100*----- 530 - 531 -----  NB JOURS INT. INTERCAL.                   00096100
096200       15 SL-NB-DGTTI-FORM-AS-X.                                  00096200
096300          20 SL-NB-DGTTI-FORM-AS        PIC 9(2).                 00096300
096400*                                                                 00096400
096500       15 FILLER                  REDEFINES SL-NB-DGTTI-FORM-AS-X.00096500
096600          20 NB-DGTTI-OORD              PIC 9(2).                 00096600
096700*                                                                 00096700
096800       15 FILLER                  REDEFINES SL-NB-DGTTI-FORM-AS-X.00096800
096900          20 SL-NB-DGTTI-OPER           PIC 9(2).                 00096900
097000*                                                                 00097000
097100*----- 532       -----  INT. INTERC. JOURN. SUR BUDGET AGENT      00097100
097200       15 SL-ST-DGTTI-FORM-AS-X.                                  00097200
097300          20 SL-ST-DGTTI-FORM-AS        PIC 9.                    00097300
097400*                                                                 00097400
097500       15 FILLER                  REDEFINES SL-ST-DGTTI-FORM-AS-X.00097500
097600          20 ST-DGTTI-OORD              PIC 9.                    00097600
097700*                                                                 00097700
097800*----- 533 - 550 -----  RESERVE                                   00097800
097900       15 FILLER                        PIC X(18).                00097900
098000*                                                                 00098000
098100*+++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++00098100
098200*-----    I N F O  D I (COUPURES/DOC. PRINCIP)    -----           00098200
098300*         ------------------------------------                    00098300
098400*----- 551 - 580 -----                                            00098400
098500    10 INFO-DI.                                                   00098500
098600*                                                                 00098600
098700*----- 551 - 556 -----  DOCUMENT DE TETE                          00098700
098800       15 NR-FIGRP-FORM-AS-R.                                     00098800
098900          20 NR-FIGRP-FORM-AS           PIC 9(6).                 00098900
099000*                                                                 00099000
099100       15 FILLER                  REDEFINES NR-FIGRP-FORM-AS-R.   00099100
099200          20 NR-FIGRP-OPER              PIC 9(6).                 00099200
099300*                                                                 00099300
099400*----- 557 - 562 -----  DOCUMENT SUIVANT                          00099400
099500       15 NR-NEGRP-FORM-AS-R.                                     00099500
099600          20 NR-NEGRP-FORM-AS           PIC 9(6).                 00099600
099700*                                                                 00099700
099800*----- 563 - 568 -----  DOCUMENT PRECEDENT                        00099800
099900       15 NR-PRGRP-FORM-AS-R.                                     00099900
100000          20 NR-PRGRP-FORM-AS           PIC 9(6).                 00100000
100100*                                                                 00100100
100200*----- 569 - 574 -----  DI MODIFIE OU NOUVEAU DI POUR ORDRE ECH.  00100200
100300       15 NEW-NR-ID-OMR.                                          00100300
100400          20 NEW-NR-ID-OMR-R            PIC 9(6).                 00100400
100500       15 NR-ID-2-RETRAIT-R       REDEFINES NEW-NR-ID-OMR.        00100500
100600          20 NR-ID-2-RETRAIT            PIC 9(6).                 00100600
100700*                                                                 00100700
100800*----- 575 - 580 -----                                            00100800
100900       15 FILLER                        PIC X(6).                 00100900
101000*                                                                 00101000
101100*+++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++00101100
101200*-----             R E G U L .                               -----00101200
101300*                  -----------                                    00101300
101400*----- 581 - 605 -----                                            00101400
101500    10 INFO-REGUL.                                                00101500
101600*                                                                 00101600
101700*----- 581 - 593 -----  NOUVEAU NO DE TITRE                       00101700
101800       15 NR-STNEW-GDIFRV.                                        00101800
101900          20 NR-STNEW-GDIFRV-NUM        PIC 9(13).                00101900
102000*                                                                 00102000
102100       15 NR-STNEW-GDIFRV-R       REDEFINES NR-STNEW-GDIFRV.      00102100
102200          20 NR-STNEW-GDIFRV-R1.                                  00102200
102300             25 NR-STNEW-GDIFRV-P1      PIC 99.                   00102300
102400             25 NR-STNEW-GDIFRV-P2      PIC 9(3).                 00102400
102500             25 FILLER        REDEFINES NR-STNEW-GDIFRV-P2.       00102500
102600                30 CT-ID-GOOD-NEW-R1    PIC 9.                    00102600
102700                30 CT-DN-GOOD-NEW-R1    PIC 9.                    00102700
102800                30 CO-LA-GOOD-NEW-R1    PIC 9.                    00102800
102900             25 NR-STNEW-GDIFRV-P3      PIC 9(7).                 00102900
103000          20 FILLER               REDEFINES NR-STNEW-GDIFRV-R1.   00103000
103100             25 NR-STNEW-GDIFRV-R2      PIC 9(12).                00103100
103200          20 NR-STNEW-GDIFRV-P4         PIC 9.                    00103200
103300*                                                                 00103300
103400       15 NR-STNEW-OORD-X         REDEFINES NR-STNEW-GDIFRV.      00103400
103500          20 NR-STNEW-OORD              PIC 9(13).                00103500
103600*                                                                 00103600
103700       15 NR-STNEW-POKB-X         REDEFINES NR-STNEW-GDIFRV.      00103700
103800          20 NR-STNEW-POKB              PIC 9(13).                00103800
103900*                                                                 00103900
104000       15 NR-STNEW-GDIFRV-OPER-X  REDEFINES NR-STNEW-GDIFRV.      00104000
104100          20 NR-STNEW-GDIFRV-OPER       PIC 9(13).                00104100
104200*                                                                 00104200
104300*----- 594 - 595 -----  NO SEQUENCE DU NOUVEAU TITRE              00104300
104400       15 NS-DB-STOCK-GDIFRV            PIC X(02).                00104400
104500*                                                                 00104500
104600       15 FILLER                  REDEFINES NS-DB-STOCK-GDIFRV.   00104600
104700          20 NS-DBSTNEW-OORD            PIC 9(2).                 00104700
104800*                                                                 00104800
104900*----- 596 - 598 -----  DERNIER COUPON PAYE                       00104900
105000       15 NS-CPAID-GDIFRV-RED.                                    00105000
105100          20 NS-CPAID-GDIFRV            PIC 9(3).                 00105100
105200*                                                                 00105200
105300       15 FILLER                  REDEFINES NS-CPAID-GDIFRV-RED.  00105300
105400          20 NS-CPAIDNW-OORD            PIC 9(3).                 00105400
105500*                                                                 00105500
105600       15 FILLER                  REDEFINES NS-CPAID-GDIFRV-RED.  00105600
105700          20 NS-CPAID-GDIFRV-OPER       PIC 9(3).                 00105700
105800*                                                                 00105800
105900*----- 599 - 602 -----  CD DERNIER COUPON PAYE                    00105900
106000       15 NR-CDCP-GDIFRV-RED.                                     00106000
106100          20 NR-CDCP-GDIFRV             PIC 9(4).                 00106100
106200*                                                                 00106200
106300       15 NR-CDCPNEW-OORD-X       REDEFINES NR-CDCP-GDIFRV-RED.   00106300
106400          20 NR-CDCPNEW-OORD            PIC 9(4).                 00106400
106500*                                                                 00106500
106600*----- 603 - 605 -----                                            00106600
106700       15 FILLER                        PIC X(3).                 00106700
106800*                                                                 00106800
106900*+++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++00106900
107000*-----      T O B - T F E - F L K  (TAXES)                        00107000
107100*           ----------------------                                00107100
107200*----- 606 - 680 -----                                            00107200
107300    10 INFO-TAX.                                                  00107300
107400*                                                                 00107400
107500*----- 606       -----  EXONÉRATION  TOB (' '=PAS/'0'=NON/'1'=OUI)00107500
107600       15 CO-EXTOB-FORM-AS              PIC X(01).                00107600
107700*                                                                 00107700
107800       15 FILLER                  REDEFINES CO-EXTOB-FORM-AS.     00107800
107900          20 CO-EXTOB-OORD              PIC X(01).                00107900
108000*                                                                 00108000
108100*----- 607       -----  PLAFOND TOB ('0'=NON/'1'=OUI)             00108100
108200       15 CO-PLTOB-FORM-AS              PIC X(01).                00108200
108300*                                                                 00108300
108400       15 FILLER                  REDEFINES CO-PLTOB-FORM-AS.     00108400
108500          20 CO-PLTOB-OORD              PIC X(01).                00108500
108600*                                                                 00108600
108700*----- 608 - 611 -----  TAUX TOB                                  00108700
108800       15 RA-TOB-FORM-AS-X.                                       00108800
108900          20 RA-TOB-FORM-AS             PIC S999V999 COMP-3.      00108900
109000*                                                                 00109000
109100       15 FILLER                  REDEFINES RA-TOB-FORM-AS-X.     00109100
109200          20 RA-TOB-OORD                PIC S999V999 COMP-3.      00109200
109300*                                                                 00109300
109400*----- 612 - 619 -----  MT TOB                                    00109400
109500       15 AM-TOB-FORM-AS-X.                                       00109500
109600          20 AM-TOB-FORM-AS             PIC S9(13)V9(2) COMP-3.   00109600
109700*                                                                 00109700
109800       15 FILLER                  REDEFINES AM-TOB-FORM-AS-X.     00109800
109900          20 AM-TOB-OORD                PIC S9(13)V9(2) COMP-3.   00109900
110000*                                                                 00110000
110100       15 FILLER                  REDEFINES AM-TOB-FORM-AS-X.     00110100
110200          20 SL-AM-TAX-OPER             PIC S9(13)V9(2) COMP-3.   00110200
110300*                                                                 00110300
110400*----- 620       -----  EXONÉRATION  TFE (' '=PAS/'0'=NON/'1'=OUI)00110400
110500       15 CO-EXTFE-FORM-AS              PIC X(01).                00110500
110600*                                                                 00110600
110700       15 FILLER                  REDEFINES CO-EXTFE-FORM-AS.     00110700
110800          20 CO-EXTFE-OORD              PIC X(01).                00110800
110900*                                                                 00110900
111000*----- 621 - 624 -----  TAUX TFE                                  00111000
111100       15 RA-TARPH-FORM-AS-X.                                     00111100
111200          20 RA-TARPH-FORM-AS           PIC S999V999 COMP-3.      00111200
111300*                                                                 00111300
111400       15 FILLER                  REDEFINES RA-TARPH-FORM-AS-X.   00111400
111500          20 RA-TARPH-OORD              PIC S999V999 COMP-3.      00111500
111600*                                                                 00111600
111700*----- 625 - 632 -----  MT TFE                                    00111700
111800       15 AM-TARPH-FORM-AS-X.                                     00111800
111900          20 AM-TARPH-FORM-AS           PIC S9(13)V9(2) COMP-3.   00111900
112000*                                                                 00112000
112100       15 FILLER                  REDEFINES AM-TARPH-FORM-AS-X.   00112100
112200          20 AM-TARPH-OORD              PIC S9(13)V9(2) COMP-3.   00112200
112300*                                                                 00112300
112400       15 FILLER                  REDEFINES AM-TARPH-FORM-AS-X.   00112400
112500          20 AM-TARPH-OPER              PIC S9(13)V9(2) COMP-3.   00112500
112600*                                                                 00112600
112700*----- 633 - 640 -----  MT BASE CALCUL TOB TFE                    00112700
112800       15 AM-BASE-FORM-AS-X.                                      00112800
112900          20 AM-BASE-FORM-AS            PIC S9(13)V9(2) COMP-3.   00112900
113000*                                                                 00113000
113100       15 FILLER                  REDEFINES AM-BASE-FORM-AS-X.    00113100
113200          20 AM-BASE-OORD               PIC S9(13)V9(2) COMP-3.   00113200
113300*                                                                 00113300
113400       15 FILLER                  REDEFINES AM-BASE-FORM-AS-X.    00113400
113500          20 AM-BASE-OPER               PIC S9(13)V9(2) COMP-3.   00113500
113600*                                                                 00113600
113700*----- 641       -----  EXONÉRATION  TFE (' '=PAS/'0'=NON/'1'=OUI)00113700
113800       15 CO-EXFLK-OORD                 PIC X(01).                00113800
113900*                                                                 00113900
114000*----- 642 - 644 -----  MT LIVRAISON PHYSIQUE AU CLIENT           00114000
114100       15 AM-FLK-FORM-AS-X.                                       00114100
114200          20 AM-FLK-FORM-AS             PIC S9(3)V9(2)  COMP-3.   00114200
114300*                                                                 00114300
114400       15 FILLER                  REDEFINES AM-FLK-FORM-AS-X.     00114400
114500          20 AM-FLK-OORD                PIC S9(3)V9(2)  COMP-3.   00114500
114600*                                                                 00114600
114700       15 FILLER                  REDEFINES AM-FLK-FORM-AS-X.     00114700
114800          20 AM-FLK-OPER                PIC S9(3)V9(2)  COMP-3.   00114800
114900*                                                                 00114900
115000*----- 645 - 652 -----  MT COMMISSION DEXIA (RACHATS)             00115000
115100       15 AM-COMDEX-OORD                PIC S9(13)V9(2)  COMP-3.  00115100
115200*                                                                 00115200
115300       15 FILLER                  REDEFINES AM-COMDEX-OORD.       00115300
115400          20 AM-COMM-OPER               PIC S9(13)V9(2)  COMP-3.  00115400
115500*                                                                 00115500
115600*----- 653 - 660 -----  MT COMMISSION AGENT (RACHATS)             00115600
115700       15 AM-COMAG-OORD                 PIC S9(13)V9(2)  COMP-3.  00115700
115800*                                                                 00115800
115900*----- 661 - 679 -----  RESERVE                                   00115900
116000       15 FILLER                        PIC X(19).                00116000
116100*                                                                 00116100
116200*+++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++  00116200
116300*----          I N F O S    P I C                         -----   00116300
116400*              ------------------                                 00116400
116500*----- 680 - 739 -----                                            00116500
116600    10 INFO-PIC.                                                  00116600
116700*                                                                 00116700
116800*----- 680 - 695 -----  N° REFERENCE VISITE CLIENT                00116800
116900       15 NR-CONTACT-OORD               PIC X(16).                00116900
117000*                                                                 00117000
117100*----- 696 - 705 -----  PERSONNE DE CONTACT                       00117100
117200       15 NR-IDACTCT-OORD               PIC X(10).                00117200
117300*                                                                 00117300
117400*----- 706 - 715 -----  CLIENT 1                                  00117400
117500       15 NR-IDACT1-OORD                PIC X(10).                00117500
117600*                                                                 00117600
117700       15 FILLER                  REDEFINES NR-IDACT1-OORD.       00117700
117800          20 NR-IDACT1-POKB             PIC X(10).                00117800
117900*                                                                 00117900
118000*----- 716 - 725 -----  CLIENT 2                                  00118000
118100       15 NR-IDACT2-OORD                PIC X(10).                00118100
118200*                                                                 00118200
118300       15 FILLER                  REDEFINES NR-IDACT2-OORD.       00118300
118400          20 NR-IDACT2-POKB             PIC X(10).                00118400
118500*                                                                 00118500
118600*----- 726       -----  TYPE DE CONTACT                           00118600
118700       15 CO-TCONTAC-OORD               PIC X.                    00118700
118800*                                                                 00118800
118900*----- 727       -----  CODE NON RESIDENT                         00118900
119000       15 CO-EXPM-OORD                  PIC X.                    00119000
119100*                                                                 00119100
119200*----- 728 - 731 -----  TAUX DE PRECOMPTE                         00119200
119300       15 RA-TI-FORM-AS-R.                                        00119300
119400          20 RA-TI-FORM-AS              PIC 99V99.                00119400
119500*                                                                 00119500
119600       15 FILLER                  REDEFINES RA-TI-FORM-AS-R.      00119600
119700          20 RA-TI-GDIFC                PIC 99V99.                00119700
119800*                                                                 00119800
119900       15 FILLER                  REDEFINES RA-TI-FORM-AS-R.      00119900
120000          20 RA-TI-OORD                 PIC 99V99.                00120000
120100*                                                                 00120100
120200       15 FILLER                  REDEFINES RA-TI-FORM-AS-R.      00120200
120300          20 RA-TI-OPER                 PIC 99V99.                00120300
120400*                                                                 00120400
120500       15 FILLER                  REDEFINES RA-TI-FORM-AS-R.      00120500
120600          20 RA-TI-COUP                 PIC 99V99.                00120600
120700*                                                                 00120700
120800       15 FILLER                  REDEFINES RA-TI-FORM-AS-R.      00120800
120900          20 RA-TI-PAY                  PIC 99V99.                00120900
121000*                                                                 00121000
121100*----- 732 - 732 ----- CODE TAXE DI RUPO                          00121100
121200       15 CO-TDR-OORD                   PIC X(1).                 00121200
                                                                        00121201
121100*----- 733 - 735 ----- TAUX THEORIQUE TAXE DI RUPO                00121202
121200       15 RA-TDR-OORD                   PIC S9(2)V9(2) COMP-3.    00121203
                                                                        00121204
121100*----- 736 - 736 ----- CODE FATCA                                 00121205
             15 CO-FATCA-OORD                 PIC X(1).                 00121206
121100*----- 737 - 739 -----                                            00121207
121200       15 FILLER                        PIC X(3).                 00121210
121300*                                                                 00121300
121400*+++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++  00121400
121500*----          R E F E R E N C E S                        -----   00121500
121600*              -------------------                                00121600
121700*----- 740 - 879 -----                                            00121700
121800    10 INFO-REF.                                                  00121800
121900*                                                                 00121900
122000*----- 740 - 765 -----  REFERENCE CUSTODY                         00122000
122100       15 NR-REFCUST-OORD               PIC X(26).                00122100
122200*                                                                 00122200
122300*----- 766 - 791 -----  TIMESTAMP REF CUSTODY                     00122300
122400       15 TS-EVTCUST-OORD               PIC X(26).                00122400
122500*                                                                 00122500
122600*----- 792 - 796 -----  N°SOLDE CUSTODY                           00122600
122700       15 NS-IDSAL-OORD                 PIC S9(8) COMP-3.         00122700
122800*                                                                 00122800
122900*----- 797 - 803 -----  NO DU TR                                  00122900
123000       15 NR-TR-FORM-AS-R.                                        00123000
123100          20 NR-TR-FORM-AS-1-6          PIC 9(6).                 00123100
123200          20 NR-TR-CD                   PIC 9.                    00123200
123300*                                                                 00123300
123400       15 FILLER                  REDEFINES NR-TR-FORM-AS-R.      00123400
123500          20 NR-TR-FORM-AS              PIC 9(7).                 00123500
123600*                                                                 00123600
123700       15 FILLER                  REDEFINES NR-TR-FORM-AS-R.      00123700
123800          20 NR-TR-OORD                 PIC 9(7).                 00123800
123900*                                                                 00123900
124000       15 FILLER                  REDEFINES NR-TR-FORM-AS-R.      00124000
124100          20 NR-RTR-OPER                PIC 9(7).                 00124100
124200*                                                                 00124200
124300*----- 804 - 808 -----  N° REF FISCALE                            00124300
124400       15 NS-REFFISC-OORD               PIC 9(9) COMP-3.          00124400
124500*                                                                 00124500
124600       15 FILLER                  REDEFINES NS-REFFISC-OORD.      00124600
124700           20 NS-TAX-OPER               PIC 9(9) COMP-3.          00124700
124800*                                                                 00124800
124900*----- 809 - 810 -----  TYPE COMPTE LIQUIDATION                   00124900
125000       15 CO-TVEREF-OORD                PIC X(2).                 00125000
125100*                                                                 00125100
125200*----- 811 - 822 -----  N° COMPTE LIQUIDATION                     00125200
125300       15 NR-ACCVER-OORD                PIC X(12).                00125300
125400*                                                                 00125400
125500*----- 823 - 831 -----  N° CAISSE LIQUIDATION CASH                00125500
125600       15 NR-KASV-OORD                  PIC X(9).                 00125600
125700*                                                                 00125700
125800*----- 832 - 857 -----  N° REFERENCE AOM                          00125800
125900       15 NR-REFAOM-OORD                PIC X(26).                00125900
126000*                                                                 00126000
126100*                                                                 00126100
126200*----- 858 - 862 -----  N° REFERENCE PHYSICAL MANAGEMENT          00126200
126300       15 NS-REF-PFLX                   PIC S9(9) COMP-3.         00126300
126400*                                                                 00126400
126500*----- 863 - 878 -----  NR-REFINT-074DORD                         00126410
126600       15 NR-REFINT-074DORD             PIC X(16).                00126420
      *                                                                 00126430
126500*----- 879 - 879 -----  FILLER                                    00126500
126600       15 FILLER                        PIC X(01).                00126600
126700*                                                                 00126700
126800*+++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++  00126800
126900*----          S T A T U S                               -----    00126900
127000*              -----------                                        00127000
127100*----- 880 - 899 -----                                            00127100
127200    10 INFO-STATUS.                                               00127200
127300*                                                                 00127300
127400*----- 880       -----  STATUS RESERVATION AOM                    00127400
127500       15 CO-STRAOM-OORD                PIC X.                    00127500
127600*                                                                 00127600
127700*----- 881       -----  STATUS CONFIRMATION AOM                   00127700
127800       15 CO-STCAOM-OORD                PIC X.                    00127800
127900*                                                                 00127900
128000*----- 882       -----  STATUS RESERVATION CUSTODY                00128000
128100       15 CO-STRCUST-OORD               PIC X.                    00128100
128200*                                                                 00128200
128300*----- 883       -----  STATUS CONFIRMATION CUSTODY               00128300
128400       15 CO-STCCUST-OORD               PIC X.                    00128400
128500*                                                                 00128500
128600*----- 884       -----  STATUS PRINT AU SIEGE                     00128600
128700       15 CO-STPRINT-OORD               PIC X.                    00128700
128800*                                                                 00128800
128900       15 FILLER                  REDEFINES CO-STPRINT-OORD.      00128900
129000          20 CO-STPRINT-POKB            PIC X.                    00129000
129100*                                                                 00129100
129200*----- 885       -----  STATUS CIRCULATION                        00129200
129300       15 CO-STCIRC-OORD                PIC X.                    00129300
129400*                                                                 00129400
129500*----- 886       -----  STATUS COMPTABILISE                       00129500
129600       15 CO-STACCT-OORD                PIC X.                    00129600
129700*                                                                 00129700
129800*----- 887       -----  STATUS TRAITEMENT BATCH                   00129800
129900       15 CO-STBATCH-OORD               PIC X.                    00129900
130000*                                                                 00130000
130100*----- 888       -----  STATUS CONTROLE SIGNATURE NÉCESSAIRE      00130100
130200       15 ST-SGNNEC-OORD                PIC X.                    00130200
130300*                                                                 00130300
130400*----- 889       -----  STATUS CONTROLE SIGNATURE EXÉCUTÉ         00130400
130500       15 ST-SGNOK-OORD                 PIC X.                    00130500
130600*                                                                 00130600
130700*----- 890       -----  STATUS REMBOURSEMENT                      00130700
130800       15 CO-STREMB                     PIC X.                    00130800
130900*                                                                 00130900
131000*----- 891 - 899 -----                                            00131000
131100       15 FILLER                        PIC X(09).                00131100
131200*                                                                 00131200
131300*+++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++  00131300
131400*----          M E S S A G E S                           -----    00131400
131500*              ---------------                                    00131500
131600*----- 900 -     -----                                            00131600
131700    10 INFO-MESS.                                                 00131700
131800*                                                                 00131800
131900*----- 900 -     -----  TYPE ERREUR                               00131900
132000       15 CO-ERRSEV-OORD                PIC X.                    00132000
132100*                                                                 00132100
132200       15 FILLER                  REDEFINES CO-ERRSEV-OORD.       00132200
132300          20 CO-SEVERITE                PIC X.                    00132300
132400*                                                                 00132400
132500*----- 901 - 904 -----  CODE ERREUR                               00132500
132600       15 CO-ERROR-OORD                 PIC X(4).                 00132600
132700*                                                                 00132700
132800       15 FILLER                  REDEFINES CO-ERROR-OORD.        00132800
132900          20 ERR-CODE                   PIC X(4).                 00132900
133000*                                                                 00133000
133100       15 FILLER                  REDEFINES CO-ERROR-OORD.        00133100
133200          20 ERR-CODE-GDIFC             PIC X(4).                 00133200
133300*                                                                 00133300
133400*----- 905 - 924 -----  INFOS ERREUR                              00133400
133500       15 TE-ERROR-OORD                 PIC X(20).                00133500
133600*                                                                 00133600
133700*----- 925 - 956 -----  RAISON ERREUR                             00133700
133800       15 TE-CAUSE-OORD                 PIC X(32).                00133800
133900*                                                                 00133900
134000*----- 957 -1056 -----  COMMENTAIRE SUR ORDRE                     00134000
134100       15 TE-COMM-OORD                  PIC X(100).               00134100
134200*                                                                 00134200
134300       15 FILLER                  REDEFINES TE-COMM-OORD.         00134300
134400          20 TE-REF-GDIFC               PIC X(100).               00134400
134500*                                                                 00134500
134600*---- 1057       -----  RAISON ECHANGE                            00134600
134700       15 CO-EXCH-OORD                  PIC X.                    00134700
134800*                                                                 00134800
134900*-----1058 -1061 -----                                            00134810
             15 NS-REFPO-074OORD              PIC 9(4).                 00134811
135100*                                                                 00134830
134900*-----1062 -1063 ----- CODE MULTI CHANNEL SIGNING                 00134900
             15 CO-POSTPON-074OORD            PIC X(2).                 00134901
      *                                                                 00134902
134900*-----1064 -1089 ----- TIMESTAMP CUT OFF SIGNATURE                00134910
             15 TS-ENDVAL-074OORD             PIC X(26).                00134911
      *                                                                 00134912
134900*-----1090 -1098 -----                                            00134920
135000       15 FILLER                        PIC X(09).                00135000
135100*                                                                 00135100
135200*+++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++  00135200
135300*----          P R I N T                                 -----    00135300
135400*              ---------                                          00135400
135500*-----1099 -1101 -----  N° LIGNE DE PRINT                         00135500
135600       15 NS-PRINT-POKB                 PIC 9(3).                 00135600
135700*                                                                 00135700
135800*-----1102 -1104 -----  NB LIGNE DE PRINT                         00135800
135900       15 NB-PRINT-POKB                 PIC 9(3).                 00135900
136000*                                                                 00136000
136100*---- 1105 -1120 -----  RESERVE                                   00136100
136200       15 FILLER                        PIC X(16).                00136200
136210*+++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++  00136210
136220*----          E F I / R F E                             -----    00136220
136230*              -------------                                      00136230
136240*-----1121 -1123 -----  THEORETISCH PERCENTAGE EFI/RFE            00136240
136250       15 RA-RFE-OORD                  PIC S9(2)V9(2) COMP-3.     00136250
136290*                                                                 00136290
136291*-----1124 -1124 -----  SWITCH VRIJSTELLING EFI/RFE               00136291
136292       15 CO-RFE-OORD                  PIC X.                     00136292
136293*                                                                 00136293
136294*-----1125 -1132 -----  BEDRAG EFI/RFE                            00136294
136295       15 AM-RFE-OORD                  PIC S9(13)V9(2) COMP-3.    00136295
136296*                                                                 00136296
136297*-----1133 -1140 -----  AANKOOPDATUM                              00136297
136298       15 DA-BUY-OORD                  PIC X(8).                  00136298
136299*                                                                 00136299
136300*-----1141 -1148 -----  MONTANT DE BASE EFI/RFE                   00136300
136301       15 AM-BASERFE-OORD              PIC S9(13)V9(2) COMP-3.    00136301
136302*                                                                 00136302
136303*---- 1149 -1200 -----  RESERVE                                   00136303
136304       15 FILLER                        PIC X(52).                00136304
136310*+++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++  00136310
136400*                                                                 00136400
