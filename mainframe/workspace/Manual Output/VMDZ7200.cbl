000100 CBL ARITH(EXTEND)                                                00000100
000200 IDENTIFICATION DIVISION.                                         00000200
000300*========================                                         00000300
000400 PROGRAM-ID. VMDZ7200.                                            00000400
000500 AUTHOR.     JAINRG 2026/05.                                      00000500
000600                                                                  00000600
000700******************************************************************00000700
000800*                                                                 00000800
000900*    ARCHIVAGE :  THIS PROGRAM IS BEING USED FOR "ARCHIVING       00000900
001000*    =========    EXTRACT FOR SUBSCRIPTION AND CANCELLATION       00001000
001100*                 FORMS" BY FETCH THE DATA FROM THE FOLLOWING     00001100
001110*                 KASBONS DB2 TABLE BY USING THE INPUT KASBONS    00001110
001120*                 DATA: DZBFASTB                                  00001120
001200******************************************************************00001200
001300                                                                  00001300
001400 ENVIRONMENT DIVISION.                                            00001400
001500*=====================                                            00001500
001600 CONFIGURATION SECTION.                                           00001600
001700*----------------------                                           00001700
001800 SPECIAL-NAMES.                                                   00001800
001900     DECIMAL-POINT IS COMMA.                                      00001900
002000*                                                                 00002000
002100 INPUT-OUTPUT SECTION.                                            00002100
002200*---------------------                                            00002200
002300 FILE-CONTROL.                                                    00002300
002400     SELECT DAARCH   ASSIGN TO UT-S-DD005.                        00002400
002500     SELECT FORM     ASSIGN TO UT-S-DD010.                        00002500
002600*                                                                 00002600
002700/                                                                 00002700
002800 DATA DIVISION.                                                   00002800
002900*==============                                                   00002900
003000 FILE SECTION.                                                    00003000
003100*-------------                                                    00003100
003200*    ----- DATE ARCHIVAGE -----                                   00003200
003300*                                                                 00003300
003400 FD  DAARCH     RECORDING F                                       00003400
003500                RECORD CONTAINS 20                                00003500
003600                BLOCK CONTAINS 0                                  00003600
003700                LABEL RECORD STANDARD.                            00003700
003800 01  DAARCH-REC                PIC X(20).                         00003800
003900*                                                                 00003900
004000*    ----- GESELECTEERDE FORMULIEREN -----                        00004000
004100*                                                                 00004100
004200 FD  FORM       RECORDING F                                       00004200
004300                RECORD CONTAINS 530                               00004300
004400                BLOCK CONTAINS 0                                  00004400
004500                LABEL RECORD STANDARD.                            00004500
004600 01  FORM-REC                  PIC X(530).                        00004600
004700/                                                                 00004700
004800*                                                                 00004800
004900 WORKING-STORAGE SECTION.                                         00004900
005000*------------------------                                         00005000
005100*                                                                 00005100
005500 77  USERABEN                  PIC X(8)          VALUE 'USERABEN'.00005500
005600 77  WS-TELLER                 PIC S9(11) COMP-3 VALUE ZERO.      00005600
005601 77  HELP-TELLER               PIC Z(11).                         00005601
005602 01  WS-DA-ARCH-YMD            PIC 9(10).                         00005602
005700*                                                                 00005700
005800 01  WS-CURSOR-FLAG            PIC X.                             00005800
005900     88  DZBFASC1-NOT-EOC                        VALUE 'N'.       00005900
006000     88  DZBFASC1-EOC                            VALUE 'Y'.       00006000
006100 01  W-NR-IS-FORM-AS           PIC 9(9).                          00006100
006200 01  FILLER REDEFINES W-NR-IS-FORM-AS.                            00006200
006300     05  W-NR-ID-ISSUE         PIC 9(7).                          00006300
006400     05  W-NR-CD-ISSUE         PIC 9(2).                          00006400
006410 01  HELP-VAR.                                                    00006410
006500     02  HULP-DA-CR-FORM-AS    PIC X(8).                          00006500
006600     02  HULP-DA-VA-FORM-AS    PIC X(8).                          00006600
006700     02  HULP-DA-UB-FORM-AS    PIC X(8).                          00006700
006800     02  HULP-DA-UE-FORM-AS    PIC X(8).                          00006800
006900     02  HULP-DA-UER-FORM-AS   PIC X(8).                          00006900
007000     02  HULP-DA-ACTVR-FORM-AS PIC X(8).                          00007000
007100     02  HULP-DA-INVTR-FORM-AS PIC X(8).                          00007100
007200     02  HULP-DA-CPTA-FORM-AS  PIC X(8).                          00007200
007400 01  REC-FORM.                                                    00007400
007500     05  F-FORM.                                                  00007500
007700       06 VMBFAS.                                                 00007700
007800          07 KY-VMBFAS.                                           00007800
007900             08 NR-RK-GOOD-V02.                                   00007900
008000                09 CT-RK-TGDSERV.                                 00008000
008100                   10 CT-RK-TGDSV           PIC X(4).             00008100
008200                   10 CT-RK-TGOOD           REDEFINES CT-RK-TGDSV 00008200
008300                                            PIC 9(4).             00008300
008400                09 GR-ID-GOOD-V02.                                00008400
008500                   10 NR-CIO-FORM-AS        PIC 9(8)       COMP-3.00008500
008600                   10 DA-CR-FORM-AS         PIC 9(8)       COMP-3.00008600
008700                   10 NR-ID-FORM-AS         PIC 9(6)       COMP-3.00008700
008800                   10 CT-OP-FORM-AS.                              00008800
008900                      12 CT-OPD-FORM-AS     PIC S9(3)      COMP-3.00008900
009000                      12 CT-OPG-FORM-AS     PIC 9(3)       COMP-3.00009000
009100                   10 FILLER                PIC X(2).             00009100
009200          07 AT-FORM-AS.                                          00009200
009300             08 NR-CIW-FORM-AS              PIC X(8).             00009300
009400             08 DA-VA-FORM-AS.                                    00009400
009500                09 DA-VA-FORM-AS-Y          PIC 9(4).             00009500
009600                09 DA-VA-FORM-AS-M          PIC 9(2).             00009600
009700                09 DA-VA-FORM-AS-D          PIC 9(2).             00009700
009800             08 CO-VM-FORM-AS               PIC X(1).             00009800
009900             08 NR-IS-FORM-AS               PIC 9(9).             00009900
010000             08 RA-RT-FORM-AS               PIC S9(3)V9(3) COMP-3.00010000
010100             08 RA-CP-FORM-AS               PIC S9(3)V9(3) COMP-3.00010100
010200             08 RA-BASE-FORM-AS             PIC S9(3)V9(3) COMP-3.00010200
010300             08 DA-UB-FORM-AS.                                    00010300
010400                09 DA-UB-FORM-AS-Y          PIC 9(4).             00010400
010500                09 DA-UB-FORM-AS-M          PIC 9(2).             00010500
010600                09 DA-UB-FORM-AS-D          PIC 9(2).             00010600
010700             08 DA-UE-FORM-AS.                                    00010700
010800                09 DA-UE-FORM-AS-Y          PIC 9(4).             00010800
010900                09 DA-UE-FORM-AS-M          PIC 9(2).             00010900
011000                09 DA-UE-FORM-AS-D          PIC 9(2).             00011000
011100             08 DU-ST-FORM-AS               PIC 9(3).             00011100
011200             08 RA-PS-FORM-AS               PIC S9(3)V9(3) COMP-3.00011200
011300             08 RA-PR-FORM-AS               PIC S9(3)V9(3) COMP-3.00011300
011400             08 AM-CNS-FORM-AS              PIC S9(13)V99  COMP-3.00011400
011500             08 AM-PS-FORM-AS               PIC S9(13)V99  COMP-3.00011500
011600             08 NB-FI-FORM-AS               PIC 9(3).             00011600
011700             08 AM-FIN-FORM-AS              PIC S9(13)V99  COMP-3.00011700
011800             08 CO-RI-FORM-AS               PIC X(1).             00011800
011900             08 NR-IDR-FORM-AS              PIC 9(6).             00011900
012000             08 DA-UER-FORM-AS.                                   00012000
012100                09 DA-UER-FORM-AS-Y         PIC 9(4).             00012100
012200                09 DA-UER-FORM-AS-M         PIC 9(2).             00012200
012300                09 DA-UER-FORM-AS-D         PIC 9(2).             00012300
012400             08 AM-FBA-FORM-AS              PIC S9(13)V99  COMP-3.00012400
012500             08 AM-FBB-FORM-AS              PIC S9(13)V99  COMP-3.00012500
012600             08 CO-RM-FORM-AS               PIC X(1).             00012600
012700             08 RA-FB-FORM-AS               PIC S9(3)V9(3) COMP-3.00012700
012800             08 NB-FB-FORM-AS               PIC 9(2).             00012800
012900             08 AM-FBN-FORM-AS              PIC S9(13)V99  COMP-3.00012900
013000             08 RA-TI-FORM-AS               PIC 9(2)V9(2).        00013000
013100             08 AM-CND-FORM-AS              PIC S9(13)V99  COMP-3.00013100
013200             08 AM-CNDN-FORM-AS             PIC S9(13)V99  COMP-3.00013200
013300             08 AM-CNSN-FORM-AS             PIC S9(13)V99  COMP-3.00013300
013400             08 NR-CD-FORM-AS               PIC 9(4).             00013400
013500             08 CT-SL-FORM-AS               PIC X(1).             00013500
013600             08 NR-ST-FORM-AS               PIC 9(13).            00013600
013700             08 CX-TW-FORM-AS               PIC X(1).             00013700
013800             08 NR-DS-FORM-AS               PIC 9(12).            00013800
013900             08 NR-IDX-FORM-AS              PIC 9(6).             00013900
014000             08 CO-LA-FORM-AS               PIC X(1).             00014000
014100             08 AM-INTER-FORM-AS            PIC S9(13)V99  COMP-3.00014100
014200             08 NB-GROUP-FORM-AS            PIC 9(3).             00014200
014300             08 NR-PRGRP-FORM-AS            PIC 9(6).             00014300
014400             08 NR-NEGRP-FORM-AS            PIC 9(6).             00014400
014500             08 NR-FIGRP-FORM-AS            PIC 9(6).             00014500
014600             08 NR-SEGRP-FORM-AS            PIC 9(3).             00014600
014700          07 NS-IDCP-FORM-AS                PIC 9(3).             00014700
014800          07 AM-CNSSP-FORM-AS               PIC S9(13)V99  COMP-3.00014800
014900          07 RA-CPTOT-FORM-AS               PIC S9(3)V9(3) COMP-3.00014900
015000          07 CO-CP-FORM-AS                  PIC X.                00015000
015100          07 CO-PERIN-FORM-AS               PIC X.                00015100
015200          07 NS-ID-FORM-AS                  PIC 9(2).             00015200
015300          07 CO-DEV-FORM-AS                 PIC X(3).             00015300
015400          07 NB-KRDEV-FORM-AS               PIC S9(6)V9(5).       00015400
015500          07 AM-BSDEV-FORM-AS               PIC S9(13)V99  COMP-3.00015500
015600          07 CO-TYP-FORM-AS                 PIC X(3).             00015600
015700          07 CO-SUBTP-FORM-AS               PIC X(3).             00015700
015800          07 CO-CONT-FORM-AS                PIC X(3).             00015800
015900          07 CO-TPVGL-FORM-AS               PIC X(2).             00015900
016000          07 AM-VGL-FORM-AS                 PIC S9(13)V99  COMP-3.00016000
016100          07 NR-PROD-FORM-AS                PIC X(4).             00016100
016200          07 DA-ACTVR-FORM-AS.                                    00016200
016300             08 DY-ACTVR-FORM-AS            PIC 9(4).             00016300
016400             08 DM-ACTVR-FORM-AS            PIC 9(2).             00016400
016500             08 DD-ACTVR-FORM-AS            PIC 9(2).             00016500
016600          07 DA-INVTR-FORM-AS.                                    00016600
016700             08 DY-INVTR-FORM-AS            PIC 9(4).             00016700
016800             08 DM-INVTR-FORM-AS            PIC 9(2).             00016800
016900             08 DD-INVTR-FORM-AS            PIC 9(2).             00016900
017000          07 RA-QZTTI-FORM-AS               PIC S9(3)V999  COMP-3.00017000
017100          07 RA-DGTTI-FORM-AS               PIC S9(3)V9(3) COMP-3.00017100
017200          07 NB-DGTTI-FORM-AS               PIC 9(2).             00017200
017300          07 AM-DGTTI-FORM-AS               PIC S9(13)V99  COMP-3.00017300
017400          07 ST-DGTTI-FORM-AS               PIC 9(1).             00017400
017500          07 ST-PRRW-FORM-AS                PIC 9(1).             00017500
017600          07 RA-GIFT-FORM-AS                PIC S9(3)V9(3) COMP-3.00017600
017700          07 AM-GIFT-FORM-AS                PIC S9(13)V99  COMP-3.00017700
017800          07 ST-VOORH-FORM-AS               PIC 9(1).             00017800
017900          07 DA-CPTA-FORM-AS.                                     00017900
018000             08 DY-CPTA-FORM-AS             PIC 9(4).             00018000
018100             08 DM-CPTA-FORM-AS             PIC 9(2).             00018100
018200             08 DD-CPTA-FORM-AS             PIC 9(2).             00018200
018300          07 CO-EXTOB-FORM-AS               PIC X(1).             00018300
018400          07 CO-PLTOB-FORM-AS               PIC X(1).             00018400
018500          07 RA-TOB-FORM-AS                 PIC S9(3)V9(3) COMP-3.00018500
018600          07 AM-TOB-FORM-AS                 PIC S9(13)V99  COMP-3.00018600
018700          07 RA-TARPH-FORM-AS               PIC S9(3)V9(3) COMP-3.00018700
018800          07 AM-TARPH-FORM-AS               PIC S9(13)V99  COMP-3.00018800
018900          07 AM-BASE-FORM-AS                PIC S9(13)V99  COMP-3.00018900
019000          07 AM-FLK-FORM-AS                 PIC S9(3)V9(2) COMP-3.00019000
019100          07 FILLER                         PIC X(0014).          00019100
019110      06 FILLER                             PIC X(0046).          00019110
019200     05  F-SW-ARCH             PIC X.                             00019200
019300     05  F-SW-VMBFGD           PIC X.                             00019300
019400     05  F-TELLER              PIC S9(11) COMP-3.                 00019400
019500     05  F-NR-IS               PIC 9(7).                          00019500
019600     05  F-NR-ST               PIC 9(13).                         00019600
019700     05  FILLER                PIC X(24).                         00019700
019900*                                                                 00019900
020000 COPY VMDZ270I.                                                   00020000
020100*                                                                 00020100
020200 01  WS-DATUMS.                                                   00020200
020210     03  DATE-NUM8                PIC 9(8) VALUE ZERO.            00020210
020300     02  DATE-YMD.                                                00020300
020400         03  D-YEAR            PIC 9(2).                          00020400
020500         03  D-MONTH           PIC 9(2).                          00020500
020600         03  D-DAY             PIC 9(2).                          00020600
020700     02  DATE-YMD8.                                               00020700
020800         03  D-CENT            PIC 9(2).                          00020800
020900         03  D-YEAR            PIC 9(2).                          00020900
021000         03  D-MONTH           PIC 9(2).                          00021000
021100         03  D-DAY             PIC 9(2).                          00021100
021200     02  DATE-DMY8.                                               00021200
021300         03  D-DAY             PIC 9(2).                          00021300
021400         03  D-MONTH           PIC 9(2).                          00021400
021500         03  D-CENT            PIC 9(2).                          00021500
021600         03  D-YEAR            PIC 9(2).                          00021600
021700 01  WS-TIMESTAMP-FIELDS.                                         00021700
021800     05 TS-SYSTEM.                                                00021800
021900        10  DA-SYS.                                               00021900
022000            15  DA-SYS-CCYY.                                      00022000
022100                20  CC            PIC X(2).                       00022100
022200                20  YY            PIC X(2).                       00022200
022300            15  MM                PIC X(2).                       00022300
022400            15  DD                PIC X(2).                       00022400
022500        10  HR-SYS.                                               00022500
022600            15  HH                PIC X(2).                       00022600
022700            15  MI                PIC X(2).                       00022700
022800            15  SS                PIC X(2).                       00022800
022900            15  TT                PIC X(2).                       00022900
023000     05 TS-TIMESTAMP.                                             00023000
023100        10  CC                    PIC X(2).                       00023100
023200        10  YY                    PIC X(2).                       00023200
023300        10  TE-MARKER1            PIC X             VALUE '-'.    00023300
023400        10  MM                    PIC X(2).                       00023400
023500        10  TE-MARKER2            PIC X             VALUE '-'.    00023500
023600        10  DD                    PIC X(2).                       00023600
023700        10  TE-MARKER3            PIC X             VALUE '-'.    00023700
023800        10  HH                    PIC X(2).                       00023800
023900        10  TE-MARKER4            PIC X             VALUE '.'.    00023900
024000        10  MI                    PIC X(2).                       00024000
024100        10  TE-MARKER5            PIC X             VALUE '.'.    00024100
024200        10  SS                    PIC X(2).                       00024200
024300        10  TE-MARKER6            PIC X             VALUE '.'.    00024300
024400        10  TT                    PIC X(2).                       00024400
024500        10  NNNN                  PIC 9(04)         VALUE 0.      00024500
024600 01 WS-DATUMVELDEN.                                               00024600
024700    03  DA-YYMMDD.                                                00024700
024800        05  YY                   PIC 99       VALUE ZERO.         00024800
024900        05  MM                   PIC 99       VALUE ZERO.         00024900
025000        05  DD                   PIC 99       VALUE ZERO.         00025000
025100    03  DA-DDMMCCYY.                                              00025100
025200        05  DD                   PIC 99       VALUE ZERO.         00025200
025300        05  MM                   PIC 99       VALUE ZERO.         00025300
025400        05  CC                   PIC 99       VALUE ZERO.         00025400
025500        05  YY                   PIC 99       VALUE ZERO.         00025500
025600    03  DA-CCYYMMDD.                                              00025600
025700        05  CC                   PIC 99       VALUE ZERO.         00025700
025800        05  YY                   PIC 99       VALUE ZERO.         00025800
025900        05  MM                   PIC 99       VALUE ZERO.         00025900
026000        05  DD                   PIC 99       VALUE ZERO.         00026000
026100    03  DA-CCYYMMDD-R REDEFINES DA-CCYYMMDD.                      00026100
026200        05  CCYY                 PIC 9999.                        00026200
026300        05  MM                   PIC 99.                          00026300
026400        05  DD                   PIC 99.                          00026400
026500    03  DA-DD-MM-CCYY.                                            00026500
026600        05  DD                   PIC 9(02).                       00026600
026700        05  TE-MARKER5           PIC X        VALUE '.'.          00026700
026800        05  MM                   PIC 9(02).                       00026800
026900        05  TE-MARKER6           PIC X        VALUE '.'.          00026900
027000        05  CCYY                 PIC 9(04).                       00027000
027100*---- INCLUDE FOR DB2 ------------------------------------------* 00027100
027200     EXEC SQL INCLUDE SQLERRWS END-EXEC.                          00027200
027300     EXEC SQL INCLUDE SQLCA    END-EXEC.                          00027300
027400                                                                  00027400
027500*---- INCLUDE VIEWS --------------------------------------------* 00027500
027600     EXEC SQL INCLUDE DZBFASTV END-EXEC.                          00027600
027700                                                                  00027700
027800*---- CURSOR DECLARATION FOR DZBFASTV --------------------------* 00027800
027900     EXEC SQL DECLARE DZBFASC1 CURSOR FOR                         00027900
028000       SELECT CT_RKTGDSV_479BFAS                                  00028000
028100            , NR_CIOFMAS_479BFAS                                  00028100
028200            , DA_CRFMAS_479BFAS                                   00028200
028300            , NR_IDFMAS_479BFAS                                   00028300
028400            , CT_OPD_479BFAS                                      00028400
028500            , CT_OPG_479BFAS                                      00028500
028600            , NR_ID_479BFAS                                       00028600
028700            , NR_CIWFMAS_479BFAS                                  00028700
028800            , DA_VAFMAS_479BFAS                                   00028800
028900            , CO_VMFMAS_479BFAS                                   00028900
029000            , NR_ISFMAS_479BFAS                                   00029000
029100            , RA_RTFMAS_479BFAS                                   00029100
029200            , RA_CPFMAS_479BFAS                                   00029200
029300            , RA_BASFMAS_479BFAS                                  00029300
029400            , DA_UBFMAS_479BFAS                                   00029400
029500            , DA_UEFMAS_479BFAS                                   00029500
029600            , DU_STFMAS_479BFAS                                   00029600
029700            , RA_PSFMAS_479BFAS                                   00029700
029800            , RA_PRFMAS_479BFAS                                   00029800
029900            , AM_CNSFMAS_479BFAS                                  00029900
030000            , AM_PSFMAS_479BFAS                                   00030000
030100            , NB_FIFMAS_479BFAS                                   00030100
030200            , AM_FINFMAS_479BFAS                                  00030200
030300            , CO_RIFMAS_479BFAS                                   00030300
030400            , NR_IDRFMAS_479BFAS                                  00030400
030500            , DA_UERFMAS_479BFAS                                  00030500
030600            , AM_FBAFMAS_479BFAS                                  00030600
030700            , AM_FBBFMAS_479BFAS                                  00030700
030800            , CO_RMFMAS_479BFAS                                   00030800
030900            , RA_FBFMAS_479BFAS                                   00030900
031000            , NB_FBFMAS_479BFAS                                   00031000
031100            , AM_FBNFMAS_479BFAS                                  00031100
031200            , RA_TIFMAS_479BFAS                                   00031200
031300            , AM_CNDFMAS_479BFAS                                  00031300
031400            , AM_CNDNFAS_479BFAS                                  00031400
031500            , AM_CNSNFAS_479BFAS                                  00031500
031600            , NR_CDFMAS_479BFAS                                   00031600
031700            , CT_SLFMAS_479BFAS                                   00031700
031800            , NR_STFMAS_479BFAS                                   00031800
031900            , CX_TWFMAS_479BFAS                                   00031900
032000            , NR_DSFMAS_479BFAS                                   00032000
032100            , NR_IDXFMAS_479BFAS                                  00032100
032200            , CO_LAFMAS_479BFAS                                   00032200
032300            , AM_INTFMAS_479BFAS                                  00032300
032400            , NB_GRPFMAS_479BFAS                                  00032400
032500            , NR_PRGRPFS_479BFAS                                  00032500
032600            , NR_NEGRPFS_479BFAS                                  00032600
032700            , NR_FIGRPFS_479BFAS                                  00032700
032800            , NR_SEGRPFS_479BFAS                                  00032800
032900            , NS_IDCPFS_479BFAS                                   00032900
033000            , AM_CNSSPFS_479BFAS                                  00033000
033100            , RA_CPTOTFS_479BFAS                                  00033100
033200            , CO_CPFMAS_479BFAS                                   00033200
033300            , CO_PERINFS_479BFAS                                  00033300
033400            , NS_IDFMAS_479BFAS                                   00033400
033500            , CO_DEVFMAS_479BFAS                                  00033500
033600            , NB_KRDEVFS_479BFAS                                  00033600
033700            , AM_BSDECFS_479BFAS                                  00033700
033800            , CO_TYPFMAS_479BFAS                                  00033800
033900            , CO_SUBTPFS_479BFAS                                  00033900
034000            , CO_CONTFS_479BFAS                                   00034000
034100            , CO_TPVGLFS_479BFAS                                  00034100
034200            , AM_VGLFMAS_479BFAS                                  00034200
034300            , NR_PRDFMAS_479BFAS                                  00034300
034400            , DA_ACTVRFS_479BFAS                                  00034400
034500            , DA_INVTRFS_479BFAS                                  00034500
034600            , RA_QZTTIFS_479BFAS                                  00034600
034700            , RA_DGTTIFS_479BFAS                                  00034700
034800            , NB_DGTTIFS_479BFAS                                  00034800
034900            , AM_DGTTIFS_479BFAS                                  00034900
035000            , ST_DGTTIFS_479BFAS                                  00035000
035100            , ST_PRRWFS_479BFAS                                   00035100
035200            , RA_GIFTFS_479BFAS                                   00035200
035300            , AM_GIFTFS_479BFAS                                   00035300
035400            , ST_VOORHFS_479BFAS                                  00035400
035500            , DA_CPTAFS_479BFAS                                   00035500
035600            , CO_EXTOBFS_479BFAS                                  00035600
035700            , CO_PLTOBFS_479BFAS                                  00035700
035800            , RA_TOBFS_479BFAS                                    00035800
035900            , AM_TOBFS_479BFAS                                    00035900
036000            , RA_TARPHFS_479BFAS                                  00036000
036100            , AM_TARPH_479BFAS                                    00036100
036200            , AM_BASEFS_479BFAS                                   00036200
036300            , AM_FLKFS_479BFAS                                    00036300
036400       FROM DZBFASTV                                              00036400
036401       WHERE (DA_CPTAFS_479BFAS < :DCLDZBFASTV.DA-CPTAFS-479BFAS  00036401
036402              AND DA_CPTAFS_479BFAS <> '01.01.0001')              00036402
036403              OR                                                  00036403
036404              (DA_CRFMAS_479BFAS < :DCLDZBFASTV.DA-CRFMAS-479BFAS 00036404
036405              AND DA_CPTAFS_479BFAS = '01.01.0001')               00036405
036406       ORDER BY NR_ID_479BFAS ASC                                 00036406
036407       FOR READ ONLY                                              00036407
036408              QUERYNO 254                                         00036408
036409     END-EXEC.                                                    00036409
037600                                                                  00037600
037700/                                                                 00037700
037800 LINKAGE SECTION.                                                 00037800
037900 01  PARAM-ZONEDO.                                                00037900
038000     02  L-PARAM          PIC S9(4)   COMP.                       00038000
038100     02  DATUMLS.                                                 00038100
038200         03  DATE-IND     PIC X.                                  00038200
038300         03  DATE8-LS     PIC 9(8).                               00038300
038400/                                                                 00038400
038500 PROCEDURE DIVISION USING PARAM-ZONEDO.                           00038500
038600*======================================                           00038600
038700     PERFORM 1000-BEGIN-PROGRAMMA THRU 1000-BEGIN-PROGRAMMA-EXIT. 00038700
038800     PERFORM 2000-TREAT-PROGRAM.                                  00038800
038900     PERFORM EINDE-PROGRAMMA THRU EINDE-PROGRAMMA-EXIT.           00038900
039000*                                                                 00039000
039100     GOBACK.                                                      00039100
039300*                                                                 00039300
039400 1000-BEGIN-PROGRAMMA.                                            00039400
039500*---------------------                                            00039500
039600     IF DATE-IND = '0'                                            00039600
039700        ACCEPT DATE-YMD         FROM DATE                         00039700
039800        MOVE CORR DATE-YMD    TO DATE-DMY8                        00039800
039900        IF D-YEAR OF DATE-YMD > 60                                00039900
040000           MOVE 19            TO D-CENT OF DATE-DMY8              00040000
040100        ELSE                                                      00040100
040200           MOVE 20            TO D-CENT OF DATE-DMY8              00040200
040300        END-IF                                                    00040300
040400     ELSE                                                         00040400
040500        MOVE DATE8-LS         TO DATE-DMY8                        00040500
040600        MOVE CORR DATE-DMY8   TO DATE-YMD                         00040600
040700     END-IF.                                                      00040700
040800     MOVE CORR DATE-DMY8      TO DATE-YMD8.                       00040800
040900                                                                  00040900
041300     OPEN INPUT  DAARCH                                           00041300
041400          OUTPUT FORM.                                            00041400
041500     READ DAARCH INTO VMDZ270I-REC                                00041500
041600          AT END                                                  00041600
041700             DISPLAY 'VMDZ7200: ** DATE ARCHIVAGE NOT OK **'      00041700
041800             CALL USERABEN.                                       00041800
042000     CLOSE DAARCH.                                                00042000
042100     MOVE 'VMDZ7200'          TO PROGRAM-NAME.                    00042100
042101     INITIALIZE DCLDZBFASTV.                                      00042101
042110     MOVE DA-ARCH-YMD OF VMDZ270I-REC TO DA-CCYYMMDD.             00042110
042191     MOVE CORR DA-CCYYMMDD-R    TO DA-DD-MM-CCYY.                 00042191
042192     MOVE DA-DD-MM-CCYY         TO WS-DA-ARCH-YMD.                00042192
042193     MOVE WS-DA-ARCH-YMD        TO DA-CPTAFS-479BFAS              00042193
042194                                OF DCLDZBFASTV.                   00042194
042195     MOVE WS-DA-ARCH-YMD        TO DA-CRFMAS-479BFAS              00042195
042196                                OF DCLDZBFASTV.                   00042196
042200*                                                                 00042200
042210 1000-BEGIN-PROGRAMMA-EXIT.                                       00042210
042220*-------------------------                                        00042220
042230     EXIT.                                                        00042230
042240*                                                                 00042240
042300 2100-OPEN-CURSOR-DZBFASC1.                                       00042300
042400*----------------------------                                     00042400
042500     EXEC SQL                                                     00042500
042600       OPEN DZBFASC1                                              00042600
042700     END-EXEC                                                     00042700
042710     EVALUATE SQLCODE                                             00042710
042720       WHEN 0                                                     00042720
042730            SET DZBFASC1-NOT-EOC TO TRUE                          00042730
042740       WHEN OTHER                                                 00042740
042750            DISPLAY 'ERROR IN OPENING THE CURSOR DZBFASC1'        00042750
042760            PERFORM SQLERROR                                      00042760
042770     END-EVALUATE                                                 00042770
042780     .                                                            00042780
044400 2200-FETCH-CURSOR-DZBFASC1.                                      00044400
044500*-----------------------------                                    00044500
044510     INITIALIZE DCLDZBFASTV.                                      00044510
044520     SET DZBFASC1-NOT-EOC TO TRUE                                 00044520
044600     EXEC SQL                                                     00044600
044700       FETCH DZBFASC1                                             00044700
044800        INTO :DCLDZBFASTV.CT-RKTGDSV-479BFAS                      00044800
044900           , :DCLDZBFASTV.NR-CIOFMAS-479BFAS                      00044900
045000           , :DCLDZBFASTV.DA-CRFMAS-479BFAS                       00045000
045100           , :DCLDZBFASTV.NR-IDFMAS-479BFAS                       00045100
045200           , :DCLDZBFASTV.CT-OPD-479BFAS                          00045200
045300           , :DCLDZBFASTV.CT-OPG-479BFAS                          00045300
045400           , :DCLDZBFASTV.NR-ID-479BFAS                           00045400
045500           , :DCLDZBFASTV.NR-CIWFMAS-479BFAS                      00045500
045600           , :DCLDZBFASTV.DA-VAFMAS-479BFAS                       00045600
045700           , :DCLDZBFASTV.CO-VMFMAS-479BFAS                       00045700
045800           , :DCLDZBFASTV.NR-ISFMAS-479BFAS                       00045800
045900           , :DCLDZBFASTV.RA-RTFMAS-479BFAS                       00045900
046000           , :DCLDZBFASTV.RA-CPFMAS-479BFAS                       00046000
046100           , :DCLDZBFASTV.RA-BASFMAS-479BFAS                      00046100
046200           , :DCLDZBFASTV.DA-UBFMAS-479BFAS                       00046200
046300           , :DCLDZBFASTV.DA-UEFMAS-479BFAS                       00046300
046400           , :DCLDZBFASTV.DU-STFMAS-479BFAS                       00046400
046500           , :DCLDZBFASTV.RA-PSFMAS-479BFAS                       00046500
046600           , :DCLDZBFASTV.RA-PRFMAS-479BFAS                       00046600
046700           , :DCLDZBFASTV.AM-CNSFMAS-479BFAS                      00046700
046800           , :DCLDZBFASTV.AM-PSFMAS-479BFAS                       00046800
046900           , :DCLDZBFASTV.NB-FIFMAS-479BFAS                       00046900
047000           , :DCLDZBFASTV.AM-FINFMAS-479BFAS                      00047000
047100           , :DCLDZBFASTV.CO-RIFMAS-479BFAS                       00047100
047200           , :DCLDZBFASTV.NR-IDRFMAS-479BFAS                      00047200
047300           , :DCLDZBFASTV.DA-UERFMAS-479BFAS                      00047300
047400           , :DCLDZBFASTV.AM-FBAFMAS-479BFAS                      00047400
047500           , :DCLDZBFASTV.AM-FBBFMAS-479BFAS                      00047500
047600           , :DCLDZBFASTV.CO-RMFMAS-479BFAS                       00047600
047700           , :DCLDZBFASTV.RA-FBFMAS-479BFAS                       00047700
047800           , :DCLDZBFASTV.NB-FBFMAS-479BFAS                       00047800
047900           , :DCLDZBFASTV.AM-FBNFMAS-479BFAS                      00047900
048000           , :DCLDZBFASTV.RA-TIFMAS-479BFAS                       00048000
048100           , :DCLDZBFASTV.AM-CNDFMAS-479BFAS                      00048100
048200           , :DCLDZBFASTV.AM-CNDNFAS-479BFAS                      00048200
048300           , :DCLDZBFASTV.AM-CNSNFAS-479BFAS                      00048300
048400           , :DCLDZBFASTV.NR-CDFMAS-479BFAS                       00048400
048500           , :DCLDZBFASTV.CT-SLFMAS-479BFAS                       00048500
048600           , :DCLDZBFASTV.NR-STFMAS-479BFAS                       00048600
048700           , :DCLDZBFASTV.CX-TWFMAS-479BFAS                       00048700
048800           , :DCLDZBFASTV.NR-DSFMAS-479BFAS                       00048800
048900           , :DCLDZBFASTV.NR-IDXFMAS-479BFAS                      00048900
049000           , :DCLDZBFASTV.CO-LAFMAS-479BFAS                       00049000
049100           , :DCLDZBFASTV.AM-INTFMAS-479BFAS                      00049100
049200           , :DCLDZBFASTV.NB-GRPFMAS-479BFAS                      00049200
049300           , :DCLDZBFASTV.NR-PRGRPFS-479BFAS                      00049300
049400           , :DCLDZBFASTV.NR-NEGRPFS-479BFAS                      00049400
049500           , :DCLDZBFASTV.NR-FIGRPFS-479BFAS                      00049500
049600           , :DCLDZBFASTV.NR-SEGRPFS-479BFAS                      00049600
049700           , :DCLDZBFASTV.NS-IDCPFS-479BFAS                       00049700
049800           , :DCLDZBFASTV.AM-CNSSPFS-479BFAS                      00049800
049900           , :DCLDZBFASTV.RA-CPTOTFS-479BFAS                      00049900
050000           , :DCLDZBFASTV.CO-CPFMAS-479BFAS                       00050000
050100           , :DCLDZBFASTV.CO-PERINFS-479BFAS                      00050100
050200           , :DCLDZBFASTV.NS-IDFMAS-479BFAS                       00050200
050300           , :DCLDZBFASTV.CO-DEVFMAS-479BFAS                      00050300
050400           , :DCLDZBFASTV.NB-KRDEVFS-479BFAS                      00050400
050500           , :DCLDZBFASTV.AM-BSDECFS-479BFAS                      00050500
050600           , :DCLDZBFASTV.CO-TYPFMAS-479BFAS                      00050600
050700           , :DCLDZBFASTV.CO-SUBTPFS-479BFAS                      00050700
050800           , :DCLDZBFASTV.CO-CONTFS-479BFAS                       00050800
050900           , :DCLDZBFASTV.CO-TPVGLFS-479BFAS                      00050900
051000           , :DCLDZBFASTV.AM-VGLFMAS-479BFAS                      00051000
051100           , :DCLDZBFASTV.NR-PRDFMAS-479BFAS                      00051100
051200           , :DCLDZBFASTV.DA-ACTVRFS-479BFAS                      00051200
051300           , :DCLDZBFASTV.DA-INVTRFS-479BFAS                      00051300
051400           , :DCLDZBFASTV.RA-QZTTIFS-479BFAS                      00051400
051500           , :DCLDZBFASTV.RA-DGTTIFS-479BFAS                      00051500
051600           , :DCLDZBFASTV.NB-DGTTIFS-479BFAS                      00051600
051700           , :DCLDZBFASTV.AM-DGTTIFS-479BFAS                      00051700
051800           , :DCLDZBFASTV.ST-DGTTIFS-479BFAS                      00051800
051900           , :DCLDZBFASTV.ST-PRRWFS-479BFAS                       00051900
052000           , :DCLDZBFASTV.RA-GIFTFS-479BFAS                       00052000
052100           , :DCLDZBFASTV.AM-GIFTFS-479BFAS                       00052100
052200           , :DCLDZBFASTV.ST-VOORHFS-479BFAS                      00052200
052300           , :DCLDZBFASTV.DA-CPTAFS-479BFAS                       00052300
052400           , :DCLDZBFASTV.CO-EXTOBFS-479BFAS                      00052400
052500           , :DCLDZBFASTV.CO-PLTOBFS-479BFAS                      00052500
052600           , :DCLDZBFASTV.RA-TOBFS-479BFAS                        00052600
052700           , :DCLDZBFASTV.AM-TOBFS-479BFAS                        00052700
052800           , :DCLDZBFASTV.RA-TARPHFS-479BFAS                      00052800
052900           , :DCLDZBFASTV.AM-TARPH-479BFAS                        00052900
053000           , :DCLDZBFASTV.AM-BASEFS-479BFAS                       00053000
053100           , :DCLDZBFASTV.AM-FLKFS-479BFAS                        00053100
053200     END-EXEC.                                                    00053200
053300                                                                  00053300
053400     EVALUATE SQLCODE                                             00053400
053500       WHEN ZERO                                                  00053500
053700            PERFORM 2300-BEHANDELING                              00053700
053800       WHEN 100                                                   00053800
053900            SET DZBFASC1-EOC TO TRUE                              00053900
054000       WHEN OTHER                                                 00054000
054100            MOVE 2200        TO SQL-LOCATION                      00054100
054200            DISPLAY 'CT-RK-TGOOD : ' CT-RKTGDSV-479BFAS           00054200
054300                                     OF DCLDZBFASTV               00054300
054400                    'NR-CIO      : ' NR-CIOFMAS-479BFAS           00054400
054500                                     OF DCLDZBFASTV               00054500
054600                    'DA-CR       : ' DA-CRFMAS-479BFAS            00054600
054700                                     OF DCLDZBFASTV               00054700
054800                    'NR-IDFMAS   : ' NR-IDFMAS-479BFAS            00054800
054900                                     OF DCLDZBFASTV               00054900
055000                    'CT-OPG      : ' CT-OPG-479BFAS               00055000
055100                                     OF DCLDZBFASTV               00055100
055200                    'CT-OPD      : ' CT-OPD-479BFAS               00055200
055300                                     OF DCLDZBFASTV               00055300
055400                    'NR-ID       : ' NR-ID-479BFAS                00055400
055500                                     OF DCLDZBFASTV               00055500
055700            PERFORM SQLERROR                                      00055700
055800     END-EVALUATE                                                 00055800
055900     .                                                            00055900
056000*                                                                 00056000
056100 2400-CLOSE-CURSOR-DZBFASC1.                                      00056100
056200*-----------------------------                                    00056200
056300     EXEC SQL                                                     00056300
056400       CLOSE DZBFASC1                                             00056400
056500     END-EXEC                                                     00056500
056600                                                                  00056600
056700     EVALUATE SQLCODE                                             00056700
056800       WHEN ZERO                                                  00056800
056900            CONTINUE                                              00056900
057000       WHEN OTHER                                                 00057000
057100            MOVE 2400 TO SQL-LOCATION                             00057100
057200            DISPLAY 'ERROR WHILE CLOSING CURSOR DZBFASC1'         00057200
057300            PERFORM SQLERROR                                      00057300
057400     END-EVALUATE                                                 00057400
057500     .                                                            00057500
057600           DISPLAY 'PROGRAM NAME   :' PROGRAM-NAME.               00057600
057700           DISPLAY 'INPUT FILE DATA:'.                            00057700
057800           DISPLAY 'DA-PARM-YMD    :' DA-PARM-YMD OF VMDZ270I-REC.00057800
057900           DISPLAY 'NB-ARCH-MM     :' NB-ARCH-YY  OF VMDZ270I-REC.00057900
058000           DISPLAY 'NB-ARCH-MM     :' NB-ARCH-MM  OF VMDZ270I-REC.00058000
058010           DISPLAY 'DA-ARCH-YMD    :' DA-ARCH-YMD OF VMDZ270I-REC.00058010
058020           MOVE WS-TELLER TO HELP-TELLER.                         00058020
058030           DISPLAY 'RECORDS FETCHED:' HELP-TELLER.                00058030
058100*                                                                 00058100
058200 2000-TREAT-PROGRAM.                                              00058200
058300*-------------------                                              00058300
058400     PERFORM 2100-OPEN-CURSOR-DZBFASC1.                           00058400
058500     PERFORM 2200-FETCH-CURSOR-DZBFASC1 UNTIL DZBFASC1-EOC.       00058500
058800     PERFORM 2400-CLOSE-CURSOR-DZBFASC1.                          00058800
058900*                                                                 00058900
059000 2300-BEHANDELING.                                                00059000
059100*-----------------                                                00059100
059110     INITIALIZE HELP-VAR.                                         00059110
059120     MOVE SPACES TO REC-FORM.                                     00059120
061700*    IF (HULP-DA-CPTA-FORM-AS < DA-ARCH-YMD  AND                  00061700
061800*        HULP-DA-CPTA-FORM-AS NOT = '00000000') OR                00061800
061900*       (HULP-DA-CR-FORM-AS  < DA-ARCH-YMD AND                    00061900
062000*        HULP-DA-CPTA-FORM-AS = '00000000')                       00062000
062100           ADD 1              TO WS-TELLER                        00062100
062200           MOVE WS-TELLER     TO F-TELLER                         00062200
062300           MOVE CT-RKTGDSV-479BFAS OF DCLDZBFASTV TO              00062300
062400                                      CT-RK-TGDSV    OF VMBFAS    00062400
062500           MOVE NR-CIOFMAS-479BFAS OF DCLDZBFASTV TO              00062500
062600                                      NR-CIO-FORM-AS OF VMBFAS    00062600
062610           MOVE DA-CRFMAS-479BFAS OF DCLDZBFASTV  TO              00062610
062611                                                 DA-DD-MM-CCYY    00062611
062620           EVALUATE TRUE                                          00062620
062630            WHEN DA-DD-MM-CCYY = '01.01.0001'                     00062630
062640             MOVE ZEROES      TO DA-CCYYMMDD-R                    00062640
062650            WHEN DA-DD-MM-CCYY = '31.12.9999'                     00062650
062660             MOVE '99999999'  TO DA-CCYYMMDD-R                    00062660
062670            WHEN OTHER                                            00062670
062680             MOVE CCYY OF DA-DD-MM-CCYY TO CCYY OF DA-CCYYMMDD-R  00062680
062690             MOVE MM   OF DA-DD-MM-CCYY TO MM   OF DA-CCYYMMDD-R  00062690
062691             MOVE DD   OF DA-DD-MM-CCYY TO DD   OF DA-CCYYMMDD-R  00062691
062692           END-EVALUATE                                           00062692
062693           MOVE DA-CCYYMMDD-R               TO HULP-DA-CR-FORM-AS.00062693
062700           MOVE HULP-DA-CR-FORM-AS TO DA-CR-FORM-AS  OF VMBFAS    00062700
063000           MOVE NR-IDFMAS-479BFAS  OF DCLDZBFASTV TO              00063000
063100                                      NR-ID-FORM-AS  OF VMBFAS    00063100
063200           MOVE CT-OPD-479BFAS     OF DCLDZBFASTV TO              00063200
063300                                      CT-OPD-FORM-AS OF VMBFAS    00063300
063400           MOVE CT-OPG-479BFAS     OF DCLDZBFASTV TO              00063400
063500                                      CT-OPG-FORM-AS OF VMBFAS    00063500
063600           MOVE NR-CIWFMAS-479BFAS OF DCLDZBFASTV TO              00063600
063700                                      NR-CIW-FORM-AS OF VMBFAS    00063700
063800           MOVE DA-VAFMAS-479BFAS OF DCLDZBFASTV                  00063800
063900                                         TO DA-DD-MM-CCYY         00063900
064000           EVALUATE TRUE                                          00064000
064100            WHEN DA-DD-MM-CCYY = '01.01.0001'                     00064100
064200              MOVE ZEROES      TO DA-CCYYMMDD-R                   00064200
064300            WHEN DA-DD-MM-CCYY = '31.12.9999'                     00064300
064400              MOVE '99999999'  TO DA-CCYYMMDD-R                   00064400
064500            WHEN OTHER                                            00064500
064600              MOVE CCYY OF DA-DD-MM-CCYY TO CCYY OF DA-CCYYMMDD-R 00064600
064700              MOVE MM   OF DA-DD-MM-CCYY TO MM   OF DA-CCYYMMDD-R 00064700
064800              MOVE DD   OF DA-DD-MM-CCYY TO DD   OF DA-CCYYMMDD-R 00064800
064900           END-EVALUATE                                           00064900
065000           MOVE DA-CCYYMMDD-R            TO HULP-DA-VA-FORM-AS    00065000
065100           MOVE HULP-DA-VA-FORM-AS       TO DA-VA-FORM-AS         00065100
065200                                                     OF VMBFAS    00065200
065300           MOVE CO-VMFMAS-479BFAS OF DCLDZBFASTV TO               00065300
065400                                       CO-VM-FORM-AS OF VMBFAS    00065400
065500           MOVE NR-ISFMAS-479BFAS OF DCLDZBFASTV TO               00065500
065600                                       NR-IS-FORM-AS OF VMBFAS    00065600
065700           MOVE RA-RTFMAS-479BFAS OF DCLDZBFASTV TO               00065700
065800                                       RA-RT-FORM-AS OF VMBFAS    00065800
065900           MOVE RA-CPFMAS-479BFAS OF DCLDZBFASTV TO               00065900
066000                                       RA-CP-FORM-AS OF VMBFAS    00066000
066100           MOVE RA-BASFMAS-479BFAS OF DCLDZBFASTV TO              00066100
066200                                     RA-BASE-FORM-AS OF VMBFAS    00066200
066300           MOVE DA-UBFMAS-479BFAS OF DCLDZBFASTV                  00066300
066400                                             TO DA-DD-MM-CCYY     00066400
066500           EVALUATE TRUE                                          00066500
066600           WHEN DA-DD-MM-CCYY = '01.01.0001'                      00066600
066700           MOVE ZEROES      TO DA-CCYYMMDD-R                      00066700
066800           WHEN DA-DD-MM-CCYY = '31.12.9999'                      00066800
066900              MOVE '99999999'  TO DA-CCYYMMDD-R                   00066900
067000           WHEN OTHER                                             00067000
067100              MOVE CCYY OF DA-DD-MM-CCYY TO CCYY OF DA-CCYYMMDD-R 00067100
067200              MOVE MM   OF DA-DD-MM-CCYY TO MM   OF DA-CCYYMMDD-R 00067200
067300              MOVE DD   OF DA-DD-MM-CCYY TO DD   OF DA-CCYYMMDD-R 00067300
067400           END-EVALUATE                                           00067400
067500           MOVE DA-CCYYMMDD-R            TO HULP-DA-UB-FORM-AS    00067500
067600           MOVE HULP-DA-UB-FORM-AS       TO DA-UB-FORM-AS         00067600
067700                                                     OF VMBFAS    00067700
067800           MOVE DA-UEFMAS-479BFAS OF DCLDZBFASTV                  00067800
067900                                         TO DA-DD-MM-CCYY         00067900
068000           EVALUATE TRUE                                          00068000
068100           WHEN DA-DD-MM-CCYY = '01.01.0001'                      00068100
068200           MOVE ZEROES      TO DA-CCYYMMDD-R                      00068200
068300           WHEN DA-DD-MM-CCYY = '31.12.9999'                      00068300
068400              MOVE '99999999'  TO DA-CCYYMMDD-R                   00068400
068500           WHEN OTHER                                             00068500
068600              MOVE CCYY OF DA-DD-MM-CCYY TO CCYY OF DA-CCYYMMDD-R 00068600
068700              MOVE MM   OF DA-DD-MM-CCYY TO MM   OF DA-CCYYMMDD-R 00068700
068800              MOVE DD   OF DA-DD-MM-CCYY TO DD   OF DA-CCYYMMDD-R 00068800
068900           END-EVALUATE                                           00068900
069000           MOVE DA-CCYYMMDD-R            TO HULP-DA-UE-FORM-AS    00069000
069100           MOVE HULP-DA-UE-FORM-AS       TO DA-UE-FORM-AS         00069100
069200                                                     OF VMBFAS    00069200
069300           MOVE DU-STFMAS-479BFAS OF DCLDZBFASTV TO               00069300
069400                                       DU-ST-FORM-AS OF VMBFAS    00069400
069500           MOVE RA-PSFMAS-479BFAS OF DCLDZBFASTV TO               00069500
069600                                       RA-PS-FORM-AS OF VMBFAS    00069600
069700           MOVE RA-PRFMAS-479BFAS OF DCLDZBFASTV TO               00069700
069800                                       RA-PR-FORM-AS OF VMBFAS    00069800
069900           MOVE AM-CNSFMAS-479BFAS OF DCLDZBFASTV TO              00069900
070000                                      AM-CNS-FORM-AS OF VMBFAS    00070000
070100           MOVE AM-PSFMAS-479BFAS OF DCLDZBFASTV TO               00070100
070200                                       AM-PS-FORM-AS OF VMBFAS    00070200
070300           MOVE NB-FIFMAS-479BFAS OF DCLDZBFASTV TO               00070300
070400                                       NB-FI-FORM-AS OF VMBFAS    00070400
070500           MOVE AM-FINFMAS-479BFAS OF DCLDZBFASTV TO              00070500
070600                                      AM-FIN-FORM-AS OF VMBFAS    00070600
070700           MOVE CO-RIFMAS-479BFAS OF DCLDZBFASTV TO               00070700
070800                                       CO-RI-FORM-AS OF VMBFAS    00070800
070900           MOVE NR-IDRFMAS-479BFAS OF DCLDZBFASTV TO              00070900
071000                                      NR-IDR-FORM-AS OF VMBFAS    00071000
071100           MOVE DA-UERFMAS-479BFAS OF DCLDZBFASTV                 00071100
071200                                            TO DA-DD-MM-CCYY      00071200
071300           EVALUATE TRUE                                          00071300
071400           WHEN DA-DD-MM-CCYY = '01.01.0001'                      00071400
071500           MOVE ZEROES      TO DA-CCYYMMDD-R                      00071500
071600           WHEN DA-DD-MM-CCYY = '31.12.9999'                      00071600
071700              MOVE '99999999'  TO DA-CCYYMMDD-R                   00071700
071800           WHEN OTHER                                             00071800
071900              MOVE CCYY OF DA-DD-MM-CCYY TO CCYY OF DA-CCYYMMDD-R 00071900
072000              MOVE MM   OF DA-DD-MM-CCYY TO MM   OF DA-CCYYMMDD-R 00072000
072100              MOVE DD   OF DA-DD-MM-CCYY TO DD   OF DA-CCYYMMDD-R 00072100
072200           END-EVALUATE                                           00072200
072300           MOVE DA-CCYYMMDD-R            TO HULP-DA-UER-FORM-AS   00072300
072400           MOVE HULP-DA-UER-FORM-AS      TO DA-UER-FORM-AS        00072400
072500                                                     OF VMBFAS    00072500
072600           MOVE AM-FBAFMAS-479BFAS       OF DCLDZBFASTV TO        00072600
072700                                      AM-FBA-FORM-AS OF VMBFAS    00072700
072800           MOVE CO-RMFMAS-479BFAS        OF DCLDZBFASTV TO        00072800
072900                                       CO-RM-FORM-AS OF VMBFAS    00072900
073000           MOVE RA-FBFMAS-479BFAS        OF DCLDZBFASTV TO        00073000
073100                                       RA-FB-FORM-AS OF VMBFAS    00073100
073200           MOVE AM-FBBFMAS-479BFAS       OF DCLDZBFASTV TO        00073200
073300                                       AM-FBB-FORM-AS OF VMBFAS   00073300
073400           MOVE CO-RMFMAS-479BFAS        OF DCLDZBFASTV TO        00073400
073500                                       CO-RM-FORM-AS OF VMBFAS    00073500
073600           MOVE RA-FBFMAS-479BFAS        OF DCLDZBFASTV TO        00073600
073700                                       RA-FB-FORM-AS OF VMBFAS    00073700
073800           MOVE NB-FBFMAS-479BFAS        OF DCLDZBFASTV TO        00073800
073900                                       NB-FB-FORM-AS OF VMBFAS    00073900
074000           MOVE AM-FBNFMAS-479BFAS       OF DCLDZBFASTV TO        00074000
074100                                       AM-FBN-FORM-AS OF VMBFAS   00074100
074200           MOVE RA-TIFMAS-479BFAS        OF DCLDZBFASTV TO        00074200
074300                                       RA-TI-FORM-AS OF VMBFAS    00074300
074400           MOVE AM-CNDFMAS-479BFAS       OF DCLDZBFASTV TO        00074400
074500                                      AM-CND-FORM-AS OF VMBFAS    00074500
074600           MOVE AM-CNDNFAS-479BFAS       OF DCLDZBFASTV TO        00074600
074700                                     AM-CNDN-FORM-AS OF VMBFAS    00074700
074800           MOVE AM-CNSNFAS-479BFAS       OF DCLDZBFASTV TO        00074800
074900                                     AM-CNSN-FORM-AS OF VMBFAS    00074900
075000           MOVE NR-CDFMAS-479BFAS        OF DCLDZBFASTV TO        00075000
075100                                      NR-CD-FORM-AS  OF VMBFAS    00075100
075200           MOVE CT-SLFMAS-479BFAS        OF DCLDZBFASTV TO        00075200
075300                                     CT-SL-FORM-AS   OF VMBFAS    00075300
075400           MOVE NR-STFMAS-479BFAS        OF DCLDZBFASTV TO        00075400
075500                                       NR-ST-FORM-AS OF VMBFAS    00075500
075600           MOVE CX-TWFMAS-479BFAS        OF DCLDZBFASTV TO        00075600
075700                                       CX-TW-FORM-AS OF VMBFAS    00075700
075800           MOVE NR-DSFMAS-479BFAS        OF DCLDZBFASTV TO        00075800
075900                                       NR-DS-FORM-AS OF VMBFAS    00075900
076000           MOVE NR-IDXFMAS-479BFAS       OF DCLDZBFASTV TO        00076000
076100                                      NR-IDX-FORM-AS OF VMBFAS    00076100
076200           MOVE CO-LAFMAS-479BFAS        OF DCLDZBFASTV TO        00076200
076300                                       CO-LA-FORM-AS OF VMBFAS    00076300
076400           MOVE AM-INTFMAS-479BFAS       OF DCLDZBFASTV TO        00076400
076500                                    AM-INTER-FORM-AS OF VMBFAS    00076500
076600           MOVE NB-GRPFMAS-479BFAS       OF DCLDZBFASTV TO        00076600
076700                                    NB-GROUP-FORM-AS OF VMBFAS    00076700
076800           MOVE NR-PRGRPFS-479BFAS       OF DCLDZBFASTV TO        00076800
076900                                    NR-PRGRP-FORM-AS OF VMBFAS    00076900
077000           MOVE NR-NEGRPFS-479BFAS       OF DCLDZBFASTV TO        00077000
077100                                    NR-NEGRP-FORM-AS OF VMBFAS    00077100
077200           MOVE NR-FIGRPFS-479BFAS       OF DCLDZBFASTV TO        00077200
077300                                    NR-FIGRP-FORM-AS OF VMBFAS    00077300
077400           MOVE NR-SEGRPFS-479BFAS       OF DCLDZBFASTV TO        00077400
077500                                    NR-SEGRP-FORM-AS OF VMBFAS    00077500
077600           MOVE NS-IDCPFS-479BFAS        OF DCLDZBFASTV TO        00077600
077700                                    NS-IDCP-FORM-AS  OF VMBFAS    00077700
077800           MOVE AM-CNSSPFS-479BFAS       OF DCLDZBFASTV TO        00077800
077900                                    AM-CNSSP-FORM-AS OF VMBFAS    00077900
078000           MOVE RA-CPTOTFS-479BFAS       OF DCLDZBFASTV TO        00078000
078100                                    RA-CPTOT-FORM-AS OF VMBFAS    00078100
078200           MOVE CO-CPFMAS-479BFAS        OF DCLDZBFASTV TO        00078200
078300                                    CO-CP-FORM-AS    OF VMBFAS    00078300
078400           MOVE CO-PERINFS-479BFAS       OF DCLDZBFASTV TO        00078400
078500                                    CO-PERIN-FORM-AS OF VMBFAS    00078500
078600           MOVE NS-IDFMAS-479BFAS        OF DCLDZBFASTV TO        00078600
078700                                    NS-ID-FORM-AS    OF VMBFAS    00078700
078800           MOVE CO-DEVFMAS-479BFAS       OF DCLDZBFASTV TO        00078800
078900                                    CO-DEV-FORM-AS   OF VMBFAS    00078900
079000           MOVE NB-KRDEVFS-479BFAS       OF DCLDZBFASTV TO        00079000
079100                                    NB-KRDEV-FORM-AS OF VMBFAS    00079100
079200           MOVE AM-BSDECFS-479BFAS       OF DCLDZBFASTV TO        00079200
079300                                    AM-BSDEV-FORM-AS OF VMBFAS    00079300
079400           MOVE CO-TYPFMAS-479BFAS       OF DCLDZBFASTV TO        00079400
079500                                    CO-TYP-FORM-AS   OF VMBFAS    00079500
079600           MOVE CO-SUBTPFS-479BFAS       OF DCLDZBFASTV TO        00079600
079700                                    CO-SUBTP-FORM-AS OF VMBFAS    00079700
079800           MOVE CO-CONTFS-479BFAS        OF DCLDZBFASTV TO        00079800
079900                                    CO-CONT-FORM-AS  OF VMBFAS    00079900
080000           MOVE CO-TPVGLFS-479BFAS       OF DCLDZBFASTV TO        00080000
080100                                    CO-TPVGL-FORM-AS OF VMBFAS    00080100
080200           MOVE AM-VGLFMAS-479BFAS       OF DCLDZBFASTV TO        00080200
080300                                    AM-VGL-FORM-AS   OF VMBFAS    00080300
080400           MOVE NR-PRDFMAS-479BFAS       OF DCLDZBFASTV TO        00080400
080500                                    NR-PROD-FORM-AS  OF VMBFAS    00080500
080600           MOVE DA-ACTVRFS-479BFAS OF DCLDZBFASTV                 00080600
080700                                           TO DA-DD-MM-CCYY       00080700
080800           EVALUATE TRUE                                          00080800
080900           WHEN DA-DD-MM-CCYY = '01.01.0001'                      00080900
081000           MOVE ZEROES      TO DA-CCYYMMDD-R                      00081000
081100           WHEN DA-DD-MM-CCYY = '31.12.9999'                      00081100
081200              MOVE '99999999'  TO DA-CCYYMMDD-R                   00081200
081300           WHEN OTHER                                             00081300
081400              MOVE CCYY OF DA-DD-MM-CCYY TO CCYY OF DA-CCYYMMDD-R 00081400
081500              MOVE MM   OF DA-DD-MM-CCYY TO MM   OF DA-CCYYMMDD-R 00081500
081600              MOVE DD   OF DA-DD-MM-CCYY TO DD   OF DA-CCYYMMDD-R 00081600
081700           END-EVALUATE                                           00081700
081800           MOVE DA-CCYYMMDD-R            TO HULP-DA-ACTVR-FORM-AS 00081800
081900           MOVE HULP-DA-ACTVR-FORM-AS    TO DA-ACTVR-FORM-AS      00081900
082000                                                     OF VMBFAS    00082000
082100           MOVE DA-INVTRFS-479BFAS OF DCLDZBFASTV                 00082100
082200                                            TO DA-DD-MM-CCYY      00082200
082300           EVALUATE TRUE                                          00082300
082400           WHEN DA-DD-MM-CCYY = '01.01.0001'                      00082400
082500           MOVE ZEROES      TO DA-CCYYMMDD-R                      00082500
082600           WHEN DA-DD-MM-CCYY = '31.12.9999'                      00082600
082700              MOVE '99999999'  TO DA-CCYYMMDD-R                   00082700
082800           WHEN OTHER                                             00082800
082900              MOVE CCYY OF DA-DD-MM-CCYY TO CCYY OF DA-CCYYMMDD-R 00082900
083000              MOVE MM   OF DA-DD-MM-CCYY TO MM   OF DA-CCYYMMDD-R 00083000
083100              MOVE DD   OF DA-DD-MM-CCYY TO DD   OF DA-CCYYMMDD-R 00083100
083200           END-EVALUATE                                           00083200
083300           MOVE DA-CCYYMMDD-R            TO HULP-DA-INVTR-FORM-AS 00083300
083400           MOVE HULP-DA-INVTR-FORM-AS    TO DA-INVTR-FORM-AS      00083400
083500                                                     OF VMBFAS    00083500
083600           MOVE RA-QZTTIFS-479BFAS       OF DCLDZBFASTV TO        00083600
083700                                    RA-QZTTI-FORM-AS OF VMBFAS    00083700
083800           MOVE RA-DGTTIFS-479BFAS       OF DCLDZBFASTV TO        00083800
083900                                    RA-DGTTI-FORM-AS OF VMBFAS    00083900
084000           MOVE NB-DGTTIFS-479BFAS       OF DCLDZBFASTV TO        00084000
084100                                    NB-DGTTI-FORM-AS OF VMBFAS    00084100
084200           MOVE AM-DGTTIFS-479BFAS       OF DCLDZBFASTV TO        00084200
084300                                    AM-DGTTI-FORM-AS OF VMBFAS    00084300
084400           MOVE ST-DGTTIFS-479BFAS       OF DCLDZBFASTV TO        00084400
084500                                    ST-DGTTI-FORM-AS OF VMBFAS    00084500
084600           MOVE ST-PRRWFS-479BFAS        OF DCLDZBFASTV TO        00084600
084700                                    ST-PRRW-FORM-AS  OF VMBFAS    00084700
084800           MOVE RA-GIFTFS-479BFAS        OF DCLDZBFASTV TO        00084800
084900                                    RA-GIFT-FORM-AS  OF VMBFAS    00084900
085000           MOVE AM-GIFTFS-479BFAS        OF DCLDZBFASTV TO        00085000
085100                                    AM-GIFT-FORM-AS  OF VMBFAS    00085100
085200           MOVE ST-VOORHFS-479BFAS       OF DCLDZBFASTV TO        00085200
085300                                    ST-VOORH-FORM-AS OF VMBFAS    00085300
085310           MOVE DA-CPTAFS-479BFAS OF DCLDZBFASTV TO               00085310
085311                                               DA-DD-MM-CCYY      00085311
085320           EVALUATE TRUE                                          00085320
085330            WHEN DA-DD-MM-CCYY = '01.01.0001'                     00085330
085340             MOVE ZEROES      TO DA-CCYYMMDD-R                    00085340
085350            WHEN DA-DD-MM-CCYY = '31.12.9999'                     00085350
085360             MOVE '99999999'  TO DA-CCYYMMDD-R                    00085360
085370            WHEN OTHER                                            00085370
085380             MOVE CCYY OF DA-DD-MM-CCYY TO CCYY OF DA-CCYYMMDD-R  00085380
085390             MOVE MM   OF DA-DD-MM-CCYY TO MM   OF DA-CCYYMMDD-R  00085390
085391             MOVE DD   OF DA-DD-MM-CCYY TO DD   OF DA-CCYYMMDD-R  00085391
085392           END-EVALUATE                                           00085392
085393           MOVE DA-CCYYMMDD-R               TO                    00085393
085394                                         HULP-DA-CPTA-FORM-AS.    00085394
085400           MOVE HULP-DA-CPTA-FORM-AS     TO DA-CPTA-FORM-AS       00085400
085500                                                     OF VMBFAS    00085500
085600           MOVE CO-EXTOBFS-479BFAS       OF DCLDZBFASTV TO        00085600
085700                                    CO-EXTOB-FORM-AS OF VMBFAS    00085700
085800           MOVE CO-PLTOBFS-479BFAS       OF DCLDZBFASTV TO        00085800
085900                                    CO-PLTOB-FORM-AS OF VMBFAS    00085900
086000           MOVE RA-TOBFS-479BFAS         OF DCLDZBFASTV TO        00086000
086100                                    RA-TOB-FORM-AS   OF VMBFAS    00086100
086200           MOVE AM-TOBFS-479BFAS          OF DCLDZBFASTV TO       00086200
086300                                    AM-TOB-FORM-AS   OF VMBFAS    00086300
086400           MOVE RA-TARPHFS-479BFAS        OF DCLDZBFASTV TO       00086400
086500                                    RA-TARPH-FORM-AS OF VMBFAS    00086500
086600           MOVE AM-TARPH-479BFAS          OF DCLDZBFASTV TO       00086600
086700                                    AM-TARPH-FORM-AS OF VMBFAS    00086700
086800           MOVE AM-BASEFS-479BFAS         OF DCLDZBFASTV TO       00086800
086900                                    AM-BASE-FORM-AS  OF VMBFAS    00086900
086910           MOVE AM-FLKFS-479BFAS          OF DCLDZBFASTV TO       00086910
086920                                    AM-FLK-FORM-AS   OF VMBFAS    00086920
087000*OTHER MOVES                                                      00087000
087100           MOVE NR-ISFMAS-479BFAS         OF DCLDZBFASTV          00087100
087200                                          TO W-NR-IS-FORM-AS      00087200
087300           MOVE W-NR-ID-ISSUE             TO F-NR-IS              00087300
087400           MOVE NR-STFMAS-479BFAS         OF DCLDZBFASTV          00087400
087500                                          TO F-NR-ST              00087500
087600           WRITE FORM-REC FROM REC-FORM                           00087600
087700           .                                                      00087700
087800*                                                                 00087800
088400 EINDE-PROGRAMMA.                                                 00088400
088500*----------------                                                 00088500
088700     CLOSE FORM.                                                  00088700
088800*                                                                 00088800
088900 EINDE-PROGRAMMA-EXIT.                                            00088900
089000*----------------                                                 00089000
089100*                                                                 00089100
089200     EXIT.                                                        00089200
089300* SQLERROR ROUTINE.                                               00089300
089400     EXEC SQL                                                     00089400
089500          INCLUDE SQLERROR                                        00089500
089600     END-EXEC.                                                    00089600
