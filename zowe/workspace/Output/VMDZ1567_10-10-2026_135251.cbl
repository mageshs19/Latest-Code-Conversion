000010 CBL ARITH(EXTEND)                                                00010000
000020 IDENTIFICATION DIVISION.                                         00020000
000030*-----------------------.                                         00030000
000040 PROGRAM-ID. VMDZ1567.                                            00040000
000050 AUTHOR.       Veerapandian.                                      00050000
000060 DATE-WRITTEN. 2026-10-10.                                        00060000
000070 DATE-COMPILED.                                                   00070000
000080                                                                  00080000
000090****************************************************************  00090000
000100*REMARKS.       AANDUIDEN BOEKING IN DB FORMULIER              *  00100000
000110*               VOOR EFFECTENDOSSIERS.                         *  00110000
000120*                                                              *  00120000
000130*COMMITS        MICHELINE BEEVERS (DATAPROCESS BELGIUM).       *  00130000
000140*                                                              *  00140000
000150*  MODIFIED BY J.CLEMENT                                       *  00150000
000160*  07/92 : AANPASSING SLIK : RECORDS 475 ---> 575              *  00160000
000170*                            VMBD510C    ---> VMBD510V         *  00170000
000180*                                                              *  00180000
000190*  MODIFIED BY S. POMPONIO                                     *  00190000
000200*  01/97 : AANPASSING EURO2000 : RECORDS 750 ---> 1050         *  00200000
000210*                                VMBD510V    ---> VMBD510X     *  00210000
000220*                                DATEPARM EN 8 POSITIONS       *  00220000
000230*                                                              *  00230000
000240*  MODIFIED BY JEROEN "JEROD" DE SCHUTTER (DOLMEN) :           *  00240000
000250*  08/2003 : AANPASSINGEN IKV. INTEGRATIEPROJECT 6212 :        *  00250000
000260*            DAISY SECURITIES KASBONS : VMBD510X --> VMBD205I  *  00260000
000270*                                                              *  00270000
000280****************************************************************  00280000
000290                                                                  00290000
000300 ENVIRONMENT DIVISION.                                            00300000
000310*--------------------.                                            00310000
000320 CONFIGURATION SECTION.                                           00320000
000330 SPECIAL-NAMES.                                                   00330000
000340     DECIMAL-POINT IS COMMA.                                      00340000
000350 INPUT-OUTPUT SECTION.                                            00350000
000360 FILE-CONTROL.                                                    00360000
000370     SELECT OPERATIES ASSIGN TO UT-S-DD010.                       00370000
000380                                                                  00380000
000390 DATA DIVISION.                                                   00390000
000400*-------------.                                                   00400000
000410 FILE SECTION.                                                    00410000
000420 FD   OPERATIES                                                   00420000
000430      BLOCK CONTAINS 0 RECORDS                                    00430000
000440      RECORD CONTAINS 1200 CHARACTERS                             00440000
000450      RECORDING F                                                 00450000
000460      LABEL RECORDS STANDARD.                                     00460000
000470 01 WS-SWITCHES.                                                  00470000
000480      02  SW-EOF                     PIC X       VALUE 'N'.       00480000
000490          88  NOT-EOF                VALUE 'N'.                   00490000
000500          88  EOF                    VALUE 'Y'.                   00500000
000510      02  WS-RECORD-FOUND            PIC X       VALUE 'N'.       00510000
000520          88  RESTART-FOUND          VALUE 'Y'.                   00520000
000530          88  RESTART-NOT-FOUND      VALUE 'N'.                   00530000
000540                                                                  00540000
000550 01  HELP-VARIABLE.                                               00550000
000560      02  WS-RESTART-REC.                                         00560000
000570          03  NB-READ                PIC 9(15)   VALUE ZERO.      00570000
000580          03  KY-RESTART             PIC X(1200) VALUE SPACES.    00580000
000590                                                                  00590000
000600      02  WS-INPUT-KASBONS           PIC X(1200) VALUE SPACES.    00600000
000610      02  WS-TELLER                  PIC 9(9)   COMP-3 VALUE ZERO.00610000
000620      02  WS-NB-INPUT-UPD-I          PIC 9(7)   COMP-3 VALUE ZERO.00620000
000630      02  WS-NB-BFAR-UPD-I           PIC S9(11) COMP-3 VALUE +0.  00630000
000640                                                                  00640000
000650 01  WS-DATE-CONVERSION.                                          00650000
000660      03  DA-YYMMDD.                                              00660000
000670          05  YY                     PIC 99            VALUE ZERO.00670000
000680          05  MM                     PIC 99            VALUE ZERO.00680000
000690          05  DD                     PIC 99            VALUE ZERO.00690000
000700      03  DA-DDMMCCYY.                                            00700000
000710          05  DD                     PIC 99            VALUE ZERO.00710000
000720          05  MM                     PIC 99            VALUE ZERO.00720000
000730          05  CC                     PIC 99            VALUE ZERO.00730000
000740          05  YY                     PIC 99            VALUE ZERO.00740000
000750      03  DA-CCYYMMDD.                                            00750000
000760          05  CC                     PIC 99            VALUE ZERO.00760000
000770          05  YY                     PIC 99            VALUE ZERO.00770000
000780          05  MM                     PIC 99            VALUE ZERO.00780000
000790          05  DD                     PIC 99            VALUE ZERO.00790000
000800      03  DA-CCYYMMDD-R REDEFINES DA-CCYYMMDD.                    00800000
000810          05  CCYY                   PIC 9999.                    00810000
000820          05  MM                     PIC 99.                      00820000
000830          05  DD                     PIC 99.                      00830000
000840      03  DA-DD-MM-CCYY.                                          00840000
000850          05  DD                     PIC 9(02).                   00850000
000860          05  TE-MARKER1             PIC X             VALUE '.'. 00860000
000870          05  MM                     PIC 9(02).                   00870000
000880          05  TE-MARKER2             PIC X             VALUE '.'. 00880000
000890          05  CCYY                   PIC 9(04).                   00890000
000900                                                                  00900000
000910 01   OPERATIES-REC             PIC X(1200).                      00910000
000920                                                                  00920000
000930                                                                  00930000
000940 WORKING-STORAGE SECTION.                                         00940000
000950 77  USERABEN                   PIC X(8) VALUE 'USERABEN'.        00950000
000960 77  CTR-REC                    PIC 9(9) VALUE 0.                 00960000
000970 77  STOP01                     PIC X(50)                         00970000
000980     VALUE '##&&VM1BD567-STOP01 ACCES DB FORMULAIRE'.             00980000
000990 77  SW-EOF                     PIC X       VALUE 'N'.            00990000
001000 77  SW-RECAB                   PIC X       VALUE 'Y'.            01000000
001010                                                                  01010000
001020 01  STOP-DATONLY.                                                01020000
001030     02  DATE-YMD.                                                01030000
001040         03  D-YEAR             PIC 99.                           01040000
001050         03  D-MONTH            PIC 99.                           01050000
001060         03  D-DAY              PIC 99.                           01060000
001070     02  DATE-DMY.                                                01070000
001080         03  D-DAY              PIC 99.                           01080000
001090         03  D-MONTH            PIC 99.                           01090000
001100         03  D-YEAR             PIC 99.                           01100000
001110     02  DATE-YMD8.                                               01110000
001120         03  D-CENT             PIC 99.                           01120000
001130         03  D-YEAR             PIC 99.                           01130000
001140         03  D-MONTH            PIC 99.                           01140000
001150         03  D-DAY              PIC 99.                           01150000
001160     02  DATE-DMY8.                                               01160000
001170         03  D-DAY              PIC 99.                           01170000
001180         03  D-MONTH            PIC 99.                           01180000
001190         03  D-CENT             PIC 99.                           01190000
001200         03  D-YEAR             PIC 99.                           01200000
001210                                                                  01210000
001220 COPY VMDZ205I.                                                   01220000
001230      EXEC SQL INCLUDE DZ01RSTV END-EXEC.008300                   01230000
001240                                                                  01240000
001250*DB2 INFRASTRUCTURE - SQLCA, INCLUDES, FLAGS                   *  01250000
001260     EXEC SQL INCLUDE SQLERRWS END-EXEC.                          01260000
001270     EXEC SQL INCLUDE SQLCA END-EXEC.                             01270000
001280     EXEC SQL INCLUDE DZBFARTV END-EXEC.                          01280000
001290                                                                  01290000
001300                                                                  01300000
001310*DB2 GENERATED TIMESTAMP AND AUDIT WORKING STORAGE                01310000
001320 77  CS-PROGRAM               PIC X(8)    VALUE 'VMDZ1567'.       01320000
001330 01 WS-TIMESTAMP-FIELDS.                                          01330000
001340     05 TS-SYSTEM.                                                01340000
001350        10  CC                  PIC X(2).                         01350000
001360        10  YY                  PIC X(2).                         01360000
001370        10  MM                  PIC X(2).                         01370000
001380        10  DD                  PIC X(2).                         01380000
001390        10  HH                  PIC X(2).                         01390000
001400        10  MI                  PIC X(2).                         01400000
001410        10  SS                  PIC X(2).                         01410000
001420        10  TT                  PIC X(2).                         01420000
001430        10  FILLER              PIC X(13).                        01430000
001440     05 TS-TIMESTAMP.                                             01440000
001450        10  CC                  PIC X(2).                         01450000
001460        10  YY                  PIC X(2).                         01460000
001470        10  TE-MARKER1          PIC X    VALUE '-'.               01470000
001480        10  MM                  PIC X(2).                         01480000
001490        10  TE-MARKER2          PIC X    VALUE '-'.               01490000
001500        10  DD                  PIC X(2).                         01500000
001510        10  TE-MARKER3          PIC X    VALUE '-'.               01510000
001520        10  HH                  PIC X(2).                         01520000
001530        10  TE-MARKER4          PIC X    VALUE '.'.               01530000
001540        10  MI                  PIC X(2).                         01540000
001550        10  TE-MARKER5          PIC X    VALUE '.'.               01550000
001560        10  SS                  PIC X(2).                         01560000
001570        10  TE-MARKER6          PIC X    VALUE '.'.               01570000
001580        10  TT                  PIC X(2).                         01580000
001590        10  NNNN                PIC 9(04) VALUE 0.                01590000
001600                                                                  01600000
001610 LINKAGE SECTION.                                                 01610000
001620 01  PARAM-DATONLY.                                               01620000
001630     03  L-PARAM                PIC S9(4) COMP.                   01630000
001640     03  DATUMLS.                                                 01640000
001650         05  DATE-IND           PIC X.                            01650000
001660         05  DATE8-LS           PIC X(8).                         01660000
001670                                                                  01670000
001680 PROCEDURE DIVISION USING PARAM-DATONLY.                          01680000
001690 100-INITIALIZE.                                                  01690000
001700*DB2: Centralized initialization (all DCLGEN groups, constants, ti01700000
001710*DB2: Redundant INITIALIZE block removed (consolidated in 100-INIT01710000
001720     MOVE CS-PROGRAM   TO PROGRAM-NAME.                           01720000
001730     PERFORM 600-GET-TIMESTAMP.                                   01730000
001740     .                                                            01740000
001750                                                                  01750000
001760                                                                  01760000
001770*--------------------------------------.                          01770000
001780*                                                                 01780000
001790* INITIALISATIE                                                   01790000
001800*                                                                 01800000
001810     PERFORM 600-GET-TIMESTAMP.                                   01810000
001820     MOVE DATE8-LS       TO DATE-DMY8.                            01820000
001830     MOVE CORR DATE-DMY8 TO DATE-YMD.                             01830000
001840     MOVE CORR DATE-DMY8 TO DATE-DMY.                             01840000
001850     MOVE CORR DATE-DMY8 TO DATE-YMD8.                            01850000
001860                                                                  01860000
001870     MOVE 'VMDZ1567' TO PROGRAM-NAME.                             01870000
001880     OPEN INPUT OPERATIES.                                        01880000
001890                                                                  01890000
001900                                                                  01900000
001910     IF NOT SW-EOF = 'Y'                                          01910000
001920        PERFORM READ-FLAT-FILE                                    01920000
001930     END-IF.                                                      01930000
001940                                                                  01940000
001950     PERFORM VERWERKING UNTIL SW-EOF = 'Y'.                       01950000
001960                                                                  01960000
001970*    ADD CTR-REC TO NS-REC-FF-IN                                  01970000
001980*    MOVE 0 TO CTR-REC.                                           01980000
001990     CLOSE OPERATIES.                                             01990000
002000     MOVE 'COMMIT' TO SQL-LOCATION.                               02000000
002010     EXEC SQL                                                     02010000
002020       COMMIT                                                     02020000
002030     END-EXEC.                                                    02030000
002040     STOP RUN.                                                    02040000
002050 600-GET-TIMESTAMP.                                               02050000
002060     MOVE FUNCTION CURRENT-DATE            TO TS-SYSTEM.          02060000
002070     MOVE CC OF TS-SYSTEM             TO CC OF TS-TIMESTAMP       02070000
002080     MOVE YY OF TS-SYSTEM             TO YY OF TS-TIMESTAMP       02080000
002090     MOVE MM OF TS-SYSTEM             TO MM OF TS-TIMESTAMP       02090000
002100     MOVE DD OF TS-SYSTEM             TO DD OF TS-TIMESTAMP       02100000
002110     MOVE HH OF TS-SYSTEM             TO HH OF TS-TIMESTAMP       02110000
002120     MOVE MI OF TS-SYSTEM             TO MI OF TS-TIMESTAMP       02120000
002130     MOVE SS OF TS-SYSTEM             TO SS OF TS-TIMESTAMP       02130000
002140     MOVE TT OF TS-SYSTEM             TO TT OF TS-TIMESTAMP       02140000
002150     DISPLAY 'TIMESTAMP: ' TS-TIMESTAMP                           02150000
002160     .                                                            02160000
002170 700-RESTART-CONTROL.                                             02170000
002180     MOVE CS-PROGRAM                                              02180000
002190     TO NM-ID-RS-PROGRAM OF DCLDZ01RSTV.                          02190000
002200     MOVE DA-DD-MM-CCYY                                           02200000
002210     TO DA-CR-RS         OF DCLDZ01RSTV.                          02210000
002220     MOVE 1                                                       02220000
002230     TO NB-ID-RS-PHASE   OF DCLDZ01RSTV.                          02230000
002240                                                                  02240000
002250     PERFORM 700-SELECT-DZ01RSTV.                                 02250000
002260                                                                  02260000
002270     EVALUATE SQLCODE                                             02270000
002280       WHEN 0     PERFORM 810-JOB-IS-RESTART                      02280000
002290       WHEN 100   PERFORM 820-WRITE-RESTART-REC                   02290000
002300       WHEN OTHER PERFORM SQLERROR                                02300000
002310     END-EVALUATE.                                                02310000
002320                                                                  02320000
002330     MOVE 0 TO WS-TELLER.                                         02330000
002340     .                                                            02340000
002350                                                                  02350000
002360                                                                  02360000
002370 700-SELECT-DZ01RSTV.                                             02370000
002380     EXEC SQL                                                     02380000
002390       SELECT  NM_ID_RS_PROGRAM                                   02390000
002400       , NB_ID_RS_PHASE                                           02400000
002410       , DA_CR_RS                                                 02410000
002420       , CO_ID_RS                                                 02420000
002430       , NB_DAY_RS                                                02430000
002440       , TE_CH_RS_DATA                                            02440000
002450       INTO  :DCLDZ01RSTV.NM-ID-RS-PROGRAM                        02450000
002460       , :DCLDZ01RSTV.NB-ID-RS-PHASE                              02460000
002470       , :DCLDZ01RSTV.DA-CR-RS                                    02470000
002480       , :DCLDZ01RSTV.CO-ID-RS                                    02480000
002490       , :DCLDZ01RSTV.NB-DAY-RS                                   02490000
002500       , :DCLDZ01RSTV.TE-CH-RS-DATA                               02500000
002510       FROM  DZ01RSTV                                             02510000
002520       WHERE NM_ID_RS_PROGRAM =                                   02520000
002530       :DCLDZ01RSTV.NM-ID-RS-PROGRAM                              02530000
002540       AND NB_ID_RS_PHASE = :DCLDZ01RSTV.NB-ID-RS-PHASE           02540000
002550       AND DA_CR_RS = :DCLDZ01RSTV.DA-CR-RS                       02550000
002560       QUERYNO 376                                                02560000
002570     END-EXEC                                                     02570000
002580                                                                  02580000
002590     EVALUATE SQLCODE                                             02590000
002600       WHEN 0                                                     02600000
002610            SET RESTART-FOUND TO TRUE                             02610000
002620       WHEN 100                                                   02620000
002630            SET RESTART-NOT-FOUND TO TRUE                         02630000
002640       WHEN OTHER                                                 02640000
002650            PERFORM SQLERROR                                      02650000
002660     END-EVALUATE                                                 02660000
002670     .                                                            02670000
002680                                                                  02680000
002690                                                                  02690000
002700 700-UPDATE-DZ01RSTV.                                             02700000
002710     EXEC SQL                                                     02710000
002720       UPDATE DZ01RSTV                                            02720000
002730       SET TE_CH_RS_DATA = :DCLDZ01RSTV.TE-CH-RS-DATA             02730000
002740       , CO_ID_RS = :DCLDZ01RSTV.CO-ID-RS                         02740000
002750       WHERE NM_ID_RS_PROGRAM =                                   02750000
002760       :DCLDZ01RSTV.NM-ID-RS-PROGRAM                              02760000
002770       AND NB_ID_RS_PHASE = :DCLDZ01RSTV.NB-ID-RS-PHASE           02770000
002780       AND DA_CR_RS = :DCLDZ01RSTV.DA-CR-RS                       02780000
002790       QUERYNO 398                                                02790000
002800     END-EXEC                                                     02800000
002810                                                                  02810000
002820     EVALUATE SQLCODE                                             02820000
002830       WHEN 0                                                     02830000
002840            CONTINUE                                              02840000
002850       WHEN OTHER                                                 02850000
002860            PERFORM SQLERROR                                      02860000
002870     END-EVALUATE                                                 02870000
002880     .                                                            02880000
002890                                                                  02890000
002900                                                                  02900000
002910 700-INSERT-DZ01RSTV.                                             02910000
002920     EXEC SQL                                                     02920000
002930       INSERT INTO DZ01RSTV                                       02930000
002940       (NM_ID_RS_PROGRAM                                          02940000
002950       ,NB_ID_RS_PHASE                                            02950000
002960       ,DA_CR_RS                                                  02960000
002970       ,CO_ID_RS                                                  02970000
002980       ,NB_DAY_RS                                                 02980000
002990       ,TE_CH_RS_DATA)                                            02990000
003000       VALUES                                                     03000000
003010       (:DCLDZ01RSTV.NM-ID-RS-PROGRAM                             03010000
003020       ,:DCLDZ01RSTV.NB-ID-RS-PHASE                               03020000
003030       ,:DCLDZ01RSTV.DA-CR-RS                                     03030000
003040       ,:DCLDZ01RSTV.CO-ID-RS                                     03040000
003050       ,:DCLDZ01RSTV.NB-DAY-RS                                    03050000
003060       ,:DCLDZ01RSTV.TE-CH-RS-DATA)                               03060000
003070       QUERYNO 442                                                03070000
003080     END-EXEC                                                     03080000
003090                                                                  03090000
003100     EVALUATE SQLCODE                                             03100000
003110       WHEN 0                                                     03110000
003120            CONTINUE                                              03120000
003130       WHEN OTHER                                                 03130000
003140            PERFORM SQLERROR                                      03140000
003150     END-EVALUATE                                                 03150000
003160     .                                                            03160000
003170 810-JOB-IS-RESTART.                                              03170000
003180     MOVE TE-CH-RS-DATA OF DCLDZ01RSTV TO WS-RESTART-REC.         03180000
003190                                                                  03190000
003200     IF CO-ID-RS OF DCLDZ01RSTV = '1'                             03200000
003210        THEN DISPLAY 'PREVIOUS RUN COMPLETE'                      03210000
003220        CONTINUE                                                  03220000
003230     ELSE DISPLAY 'RESUMING FROM CHECKPOINT: '                    03230000
003240        MOVE NB-READ OF WS-RESTART-REC                            03240000
003250        TO WS-NB-INPUT-REC                                        03250000
003260     END-IF.                                                      03260000
003270     .                                                            03270000
003280                                                                  03280000
003290                                                                  03290000
003300 820-WRITE-RESTART-REC.                                           03300000
003310     MOVE '0'                TO CO-ID-RS OF DCLDZ01RSTV.          03310000
003320     MOVE 7                  TO NB-DAY-RS OF DCLDZ01RSTV.         03320000
003330     MOVE 1215               TO NB-READ OF WS-RESTART-REC.        03330000
003340     MOVE ZERO               TO WS-NB-INPUT-REC.                  03340000
003350     MOVE WS-RESTART-REC                                          03350000
003360     TO TE-CH-RS-DATA OF DCLDZ01RSTV.                             03360000
003370                                                                  03370000
003380     PERFORM 700-INSERT-DZ01RSTV.                                 03380000
003390                                                                  03390000
003400     DISPLAY 'STARTING NEW RUN - RESTART RECORD CREATED'.         03400000
003410     .                                                            03410000
003420                                                                  03420000
003430                                                                  03430000
003440 800-PROCESS-COMMIT.                                              03440000
003450     IF SW-EOF = 'Y'                                              03450000
003460        THEN MOVE '1'           TO CO-ID-RS OF DCLDZ01RSTV        03460000
003470     ELSE MOVE '0'           TO CO-ID-RS OF DCLDZ01RSTV           03470000
003480     END-IF.                                                      03480000
003490                                                                  03490000
003500     MOVE WS-RESTART-REC                                          03500000
003510     TO TE-CH-RS-DATA OF DCLDZ01RSTV.                             03510000
003520                                                                  03520000
003530     PERFORM 700-UPDATE-DZ01RSTV.                                 03530000
003540                                                                  03540000
003550     EXEC SQL                                                     03550000
003560       COMMIT                                                     03560000
003570     END-EXEC.                                                    03570000
003580                                                                  03580000
003590     EVALUATE SQLCODE                                             03590000
003600       WHEN 0                                                     03600000
003610            ADD 1 TO WS-COMMIT-COUNTER                            03610000
003620       WHEN OTHER                                                 03620000
003630            PERFORM SQLERROR                                      03630000
003640     END-EVALUATE.                                                03640000
003650     .                                                            03650000
003660                                                                  03660000
003670                                                                  03670000
003680                                                                  03680000
003690                                                                  03690000
003700 VERWERKING.                                                      03700000
003710     MOVE 1815 TO CT-TGDSERV-479BFAR OF DCLDZBFARTV               03710000
003720     MOVE NR-CIO-FORM-AS-R TO NR-CIOFMAS-479BFAR OF DCLDZBFARTV   03720000
003730     MOVE DA-CREA-FORM-AS-R TO DA-CRFMAS-479BFAR OF DCLDZBFARTV   03730000
003740     MOVE NR-ID-FORM-AS OF VMDZ205I TO                            03740000
003750    DCLDZBFARTV.NR-IDFMAS-479BFAR                                 03750000
003760     OF DCLDZBFARTV                                               03760000
003770     MOVE CT-OPG-FORM-AS-R TO CT-OPGFMAS-479BFAR OF DCLDZBFARTV   03770000
003780     MOVE CT-OPD-FORM-AS-R TO CT-OPDFMAS-479BFAR OF DCLDZBFARTV   03780000
003790     MOVE ZEROES TO DA-CCYYMMDD                                   03790000
003800     MOVE DATE-YMD8 TO DA-CCYYMMDD                                03800000
003810     IF DA-CCYYMMDD = ZERO OR DA-CCYYMMDD = SPACES                03810000
003820        MOVE 00010101 TO DA-CCYYMMDD                              03820000
003830     END-IF                                                       03830000
003840     MOVE CORR DA-CCYYMMDD-R TO DA-DD-MM-CCYY                     03840000
003850     MOVE DA-DD-MM-CCYY TO DCLDZBFARTV.DA-INFSDGD-479BFAR         03850000
003860     MOVE TS-TIMESTAMP TO TS-UPDATE-479BFAR OF DCLDZBFARTV.       03860000
003870     MOVE CS-PROGRAM TO ID-USERID-479BFAR OF DCLDZBFARTV.         03870000
003880*DB2: Converted MODIFY for VMBFAR.                                03880000
003890     MOVE 'UPDATE-VMBFAR' TO SQL-LOCATION.                        03890000
003900     EXEC SQL                                                     03900000
003910       UPDATE DZBFARTV                                            03910000
003920       SET                                                        03920000
003930       DA_INFSDGD_479BFAR = :DCLDZBFARTV.DA-INFSDGD-479BFAR,      03930000
003940       TS_UPDATE_479BFAR = :DCLDZBFARTV.TS-UPDATE-479BFAR,        03940000
003950       ID_USERID_479BFAR = :DCLDZBFARTV.ID-USERID-479BFAR         03950000
003960       WHERE                                                      03960000
003970       CT_TGDSERV_479BFAR = :DCLDZBFARTV.CT-TGDSERV-479BFAR       03970000
003980       AND NR_CIOFMAS_479BFAR = :DCLDZBFARTV.NR-CIOFMAS-479BFAR   03980000
003990       AND DA_CRFMAS_479BFAR = :DCLDZBFARTV.DA-CRFMAS-479BFAR     03990000
004000       AND NR_IDFMAS_479BFAR = :DCLDZBFARTV.NR-IDFMAS-479BFAR     04000000
004010       AND CT_OPDFMAS_479BFAR = :DCLDZBFARTV.CT-OPDFMAS-479BFAR   04010000
004020       AND CT_OPGFMAS_479BFAR = :DCLDZBFARTV.CT-OPGFMAS-479BFAR   04020000
004030       QUERYNO 442                                                04030000
004040     END-EXEC                                                     04040000
004050     EVALUATE SQLCODE                                             04050000
004060       WHEN 0                                                     04060000
004070            CONTINUE                                              04070000
004080       WHEN OTHER                                                 04080000
004090            DISPLAY 'ERROR ON UPDATE DZBFARTV'                    04090000
004100            PERFORM SQLERROR                                      04100000
004110     END-EVALUATE                                                 04110000
004120     .                                                            04120000
004130     EXEC SQL                                                     04130000
004140       COMMIT                                                     04140000
004150     END-EXEC.                                                    04150000
004160     END-IF.                                                      04160000
004170                                                                  04170000
004180*    LEZEN VAN DE INVOER                                          04180000
004190     PERFORM READ-FLAT-FILE.                                      04190000
004200                                                                  04200000
004210                                                                  04210000
004220 READ-FLAT-FILE.                                                  04220000
004230*---------------                                                  04230000
004240     READ OPERATIES INTO VMDZ205I                                 04240000
004250        AT END MOVE 'Y' TO SW-EOF.                                04250000
004260                                                                  04260000
004270                                                                  04270000
004280                                                                  04280000
004290*SQLERROR ROUTINE.                                                04290000
004300        EXEC SQL                                                  04300000
004310          INCLUDE SQLERROR                                        04310000
004320        END-EXEC.                                                 04320000
