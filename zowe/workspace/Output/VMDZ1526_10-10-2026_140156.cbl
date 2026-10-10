000010 CBL ARITH(EXTEND)                                                00010000
000020 IDENTIFICATION DIVISION.                                         00020000
000030*------------------------                                         00030000
000040 PROGRAM-ID. VMDZ1526.                                            00040000
000050 AUTHOR.       Veerapandian.                                      00050000
000060 DATE-WRITTEN. 2026-10-10.                                        00060000
000070 DATE-COMPILED.                                                   00070000
000080                                                                  00080000
000090*************************************************************     00090000
000100*                                                           *     00100000
000110*  VERSIE IKB2BIS MET NIEUWE TYPES                          *     00110000
000120*  NEERLEGING - VERNIETIGINGEN EFFECT                       *     00120000
000130*                                                           *     00130000
000140* MODIFIED BY J. CLEMENT : INPUT 400 ---> 600               *     00140000
000150*                          VMBD205A  ---> VMBD205S          *     00150000
000160*                                                           *     00160000
000170* MODIFIED BY P. VERBEEK : AANPASSINGEN JAAR 2000           *     00170000
000180*                                                           *     00180000
000190* MODIFIED BY S. POMPONIO: AANPASSINGEN EURO2000            *     00190000
000200*                          INPUT 600 ---> 800               *     00200000
000210*                          VMBD205S  ---> VMBD205X          *     00210000
000220* MODIFIED BY JEROEN "JEROD" DE SCHUTTER (DOLMEN) - 09/2003 *     00220000
000230*  . AANPASSINGEN IKV. INTEGRATIEPROJECT 6212 :             *     00230000
000240*    DAISY SECURITIES KASBONS                               *     00240000
000250*                                                           *     00250000
000260*************************************************************     00260000
000270                                                                  00270000
000280 ENVIRONMENT DIVISION.                                            00280000
000290*---------------------                                            00290000
000300 CONFIGURATION SECTION.                                           00300000
000310 SOURCE-COMPUTER. IBM-370.                                        00310000
000320 OBJECT-COMPUTER. IBM-370.                                        00320000
000330                                                                  00330000
000340 INPUT-OUTPUT SECTION.                                            00340000
000350 FILE-CONTROL.                                                    00350000
000360     SELECT INFIL ASSIGN TO UT-S-DD020.                           00360000
000370                                                                  00370000
000380                                                                  00380000
000390 DATA DIVISION.                                                   00390000
000400*--------------                                                   00400000
000410 FILE SECTION.                                                    00410000
000420 FD  INFIL                                                        00420000
000430     BLOCK CONTAINS 0 RECORDS                                     00430000
000440     LABEL RECORD IS STANDARD                                     00440000
000450     RECORDING MODE F                                             00450000
000460     DATA RECORD IS VMDZ205I.                                     00460000
000470                                                                  00470000
000480     COPY VMDZ205I.                                               00480000
000490      EXEC SQL INCLUDE DZ01RSTV END-EXEC.005100                   00490000
000500                                                                  00500000
000510 WORKING-STORAGE SECTION.                                         00510000
000520                                                                  00520000
000530 01 WS-SWITCHES.                                                  00530000
000540      02  SW-EOF                     PIC X       VALUE 'N'.       00540000
000550          88  NOT-EOF                VALUE 'N'.                   00550000
000560          88  EOF                    VALUE 'Y'.                   00560000
000570      02  WS-RECORD-FOUND            PIC X       VALUE 'N'.       00570000
000580          88  RESTART-FOUND          VALUE 'Y'.                   00580000
000590          88  RESTART-NOT-FOUND      VALUE 'N'.                   00590000
000600                                                                  00600000
000610 01  HELP-VARIABLE.                                               00610000
000620      02  WS-RESTART-REC.                                         00620000
000630          03  NB-READ                PIC 9(15)   VALUE ZERO.      00630000
000640          03  KY-RESTART             PIC X(1200) VALUE SPACES.    00640000
000650                                                                  00650000
000660      02  WS-INPUT-KASBONS           PIC X(1200) VALUE SPACES.    00660000
000670      02  WS-TELLER                  PIC 9(9)   COMP-3 VALUE ZERO.00670000
000680      02  WS-NB-INPUT-UPD-I          PIC 9(7)   COMP-3 VALUE ZERO.00680000
000690      02  WS-NB-BFAR-UPD-I           PIC S9(11) COMP-3 VALUE +0.  00690000
000700                                                                  00700000
000710 01  WS-DATE-CONVERSION.                                          00710000
000720      03  DA-YYMMDD.                                              00720000
000730          05  YY                     PIC 99            VALUE ZERO.00730000
000740          05  MM                     PIC 99            VALUE ZERO.00740000
000750          05  DD                     PIC 99            VALUE ZERO.00750000
000760      03  DA-DDMMCCYY.                                            00760000
000770          05  DD                     PIC 99            VALUE ZERO.00770000
000780          05  MM                     PIC 99            VALUE ZERO.00780000
000790          05  CC                     PIC 99            VALUE ZERO.00790000
000800          05  YY                     PIC 99            VALUE ZERO.00800000
000810      03  DA-CCYYMMDD.                                            00810000
000820          05  CC                     PIC 99            VALUE ZERO.00820000
000830          05  YY                     PIC 99            VALUE ZERO.00830000
000840          05  MM                     PIC 99            VALUE ZERO.00840000
000850          05  DD                     PIC 99            VALUE ZERO.00850000
000860      03  DA-CCYYMMDD-R REDEFINES DA-CCYYMMDD.                    00860000
000870          05  CCYY                   PIC 9999.                    00870000
000880          05  MM                     PIC 99.                      00880000
000890          05  DD                     PIC 99.                      00890000
000900      03  DA-DD-MM-CCYY.                                          00900000
000910          05  DD                     PIC 9(02).                   00910000
000920          05  TE-MARKER1             PIC X             VALUE '.'. 00920000
000930          05  MM                     PIC 9(02).                   00930000
000940          05  TE-MARKER2             PIC X             VALUE '.'. 00940000
000950          05  CCYY                   PIC 9(04).                   00950000
000960                                                                  00960000
000970 01  WS-HULPVELDEN.                                               00970000
000980     05  SW-EOF              VALUE +0          PIC S9    COMP.    00980000
000990         88 EOF              VALUE +1.                            00990000
001000     05  SW-FFRECAB          VALUE +0          PIC S9    COMP.    01000000
001010         88 FFRECAB-AANW     VALUE +0.                            01010000
001020  05  TELLER                                PIC 9(5) VALUE ZEROES.01020000
001030     05  USERABEN            VALUE 'USERABEN'  PIC X(8).          01030000
001040                                                                  01040000
001050 01  HULP-NR-ID-GOOD.                                             01050000
001060     03  HULP-NR-CIO     PIC 9(8)    VALUE ZEROES.                01060000
001070     03  HULP-DA-CREA    PIC 9(8)    VALUE ZEROES.                01070000
001080     03  HULP-NR-ID      PIC 9(6)    VALUE ZEROES.                01080000
001090     03  HULP-CT-OPD     PIC 999     VALUE ZEROES.                01090000
001100     03  HULP-CT-OPG     PIC 999     VALUE ZEROES.                01100000
001110 01  STOP-DATONLY.                                                01110000
001120     02  DATE-YMD.                                                01120000
001130         03  D-YEAR      PIC 99.                                  01130000
001140         03  D-MONTH     PIC 99.                                  01140000
001150         03  D-DAY       PIC 99.                                  01150000
001160     02  DATE-DMY.                                                01160000
001170         03  D-DAY       PIC 99.                                  01170000
001180         03  D-MONTH     PIC 99.                                  01180000
001190         03  D-YEAR      PIC 99.                                  01190000
001200     02  DATE-YMD8.                                               01200000
001210         03  D-CENT      PIC 99.                                  01210000
001220         03  D-YEAR      PIC 99.                                  01220000
001230         03  D-MONTH     PIC 99.                                  01230000
001240         03  D-DAY       PIC 99.                                  01240000
001250     02  DATE-DMY8.                                               01250000
001260         03  D-DAY       PIC 99.                                  01260000
001270         03  D-MONTH     PIC 99.                                  01270000
001280         03  D-CENT      PIC 99.                                  01280000
001290         03  D-YEAR      PIC 99.                                  01290000
001300                                                                  01300000
001310                                                                  01310000
001320*DB2 INFRASTRUCTURE - SQLCA, INCLUDES, FLAGS                   *  01320000
001330     EXEC SQL INCLUDE SQLERRWS END-EXEC.                          01330000
001340     EXEC SQL INCLUDE SQLCA END-EXEC.                             01340000
001350     EXEC SQL INCLUDE DZEVEFTV END-EXEC.                          01350000
001360     EXEC SQL INCLUDE DZBEFFTV END-EXEC.                          01360000
001370                                                                  01370000
001380*DB2 CURSOR END-OF-CURSOR FLAGS                                *  01380000
001390 01  WS-DZEVEFC1-FLAG               PIC X.                        01390000
001400     88  DZEVEFC1-NOT-EOC           VALUE 'N'.                    01400000
001410     88  DZEVEFC1-EOC               VALUE 'Y'.                    01410000
001420                                                                  01420000
001430                                                                  01430000
001440*DB2 CURSOR DECLARATIONS                                       *  01440000
001450     EXEC SQL                                                     01450000
001460       DECLARE DZEVEFC1 CURSOR WITH HOLD FOR                      01460000
001470       SELECT                                                     01470000
001480         CT_RKTEVPR_479EVEF                                       01480000
001490        , CT_RKTGDSV_479EVEF                                      01490000
001500        , DA_CREVTPD_479EVEF                                      01500000
001510        , NR_IDGOOD_479EVEF                                       01510000
001520        , NR_ID_479EVEF                                           01520000
001530       FROM DZEVEFTV                                              01530000
001540       ORDER BY                                                   01540000
001550         NR_ID_479EVEF DESC                                       01550000
001560       FOR READ ONLY                                              01560000
001570       QUERYNO 254                                                01570000
001580     END-EXEC.                                                    01580000
001590                                                                  01590000
001600                                                                  01600000
001610*DB2 GENERATED TIMESTAMP AND AUDIT WORKING STORAGE                01610000
001620 77  CS-PROGRAM               PIC X(8)    VALUE 'VMDZ1526'.       01620000
001630 01 WS-TIMESTAMP-FIELDS.                                          01630000
001640     05 TS-SYSTEM.                                                01640000
001650        10  CC                  PIC X(2).                         01650000
001660        10  YY                  PIC X(2).                         01660000
001670        10  MM                  PIC X(2).                         01670000
001680        10  DD                  PIC X(2).                         01680000
001690        10  HH                  PIC X(2).                         01690000
001700        10  MI                  PIC X(2).                         01700000
001710        10  SS                  PIC X(2).                         01710000
001720        10  TT                  PIC X(2).                         01720000
001730        10  FILLER              PIC X(13).                        01730000
001740     05 TS-TIMESTAMP.                                             01740000
001750        10  CC                  PIC X(2).                         01750000
001760        10  YY                  PIC X(2).                         01760000
001770        10  TE-MARKER1          PIC X    VALUE '-'.               01770000
001780        10  MM                  PIC X(2).                         01780000
001790        10  TE-MARKER2          PIC X    VALUE '-'.               01790000
001800        10  DD                  PIC X(2).                         01800000
001810        10  TE-MARKER3          PIC X    VALUE '-'.               01810000
001820        10  HH                  PIC X(2).                         01820000
001830        10  TE-MARKER4          PIC X    VALUE '.'.               01830000
001840        10  MI                  PIC X(2).                         01840000
001850        10  TE-MARKER5          PIC X    VALUE '.'.               01850000
001860        10  SS                  PIC X(2).                         01860000
001870        10  TE-MARKER6          PIC X    VALUE '.'.               01870000
001880        10  TT                  PIC X(2).                         01880000
001890        10  NNNN                PIC 9(04) VALUE 0.                01890000
001900                                                                  01900000
001910                                                                  01910000
001920*DB2 GENERATED ROW COUNTERS                                       01920000
001930 01  WS-DB2-COUNTERS.                                             01930000
001940     10  WS-NB-EVEF-COUNT         PIC 9(7)    COMP-3 VALUE ZEROES.01940000
001950 LINKAGE SECTION.                                                 01950000
001960 01  PARAM-DATONLY.                                               01960000
001970     03 L-PARAM          PIC S9(4)  COMP.                         01970000
001980     03 DATUMLS.                                                  01980000
001990        05 DAT-IND       PIC X.                                   01990000
002000        05 DATE8-LS      PIC X(8).                                02000000
002010                                                                  02010000
002020 PROCEDURE DIVISION USING PARAM-DATONLY.                          02020000
002030 100-INITIALIZE.                                                  02030000
002040*DB2: Centralized initialization (all DCLGEN groups, constants, ti02040000
002050*DB2: Redundant INITIALIZE block removed (consolidated in 100-INIT02050000
002060     MOVE CS-PROGRAM   TO PROGRAM-NAME.                           02060000
002070     PERFORM 600-GET-TIMESTAMP.                                   02070000
002080     .                                                            02080000
002090                                                                  02090000
002100                                                                  02100000
002110*---------------------------------------                          02110000
002120     PERFORM 600-GET-TIMESTAMP.                                   02120000
002130                                                                  02130000
002140 000-STUUR.                                                       02140000
002150     PERFORM 100-INITIALISATIE.                                   02150000
002160     PERFORM 200-VERWERK-INFIL UNTIL EOF.                         02160000
002170     PERFORM 800-TEST-FFRECAB.                                    02170000
002180     MOVE 'COMMIT' TO SQL-LOCATION.                               02180000
002190     EXEC SQL                                                     02190000
002200       COMMIT                                                     02200000
002210     END-EXEC.                                                    02210000
002220     CLOSE INFIL.                                                 02220000
002230     DISPLAY 'TOTAL EVEF RECORDS   : ' WS-NB-EVEF-COUNT           02230000
002240                                                                  02240000
002250     STOP RUN.                                                    02250000
002260 600-GET-TIMESTAMP.                                               02260000
002270     MOVE FUNCTION CURRENT-DATE            TO TS-SYSTEM.          02270000
002280     MOVE CC OF TS-SYSTEM             TO CC OF TS-TIMESTAMP       02280000
002290     MOVE YY OF TS-SYSTEM             TO YY OF TS-TIMESTAMP       02290000
002300     MOVE MM OF TS-SYSTEM             TO MM OF TS-TIMESTAMP       02300000
002310     MOVE DD OF TS-SYSTEM             TO DD OF TS-TIMESTAMP       02310000
002320     MOVE HH OF TS-SYSTEM             TO HH OF TS-TIMESTAMP       02320000
002330     MOVE MI OF TS-SYSTEM             TO MI OF TS-TIMESTAMP       02330000
002340     MOVE SS OF TS-SYSTEM             TO SS OF TS-TIMESTAMP       02340000
002350     MOVE TT OF TS-SYSTEM             TO TT OF TS-TIMESTAMP       02350000
002360     DISPLAY 'TIMESTAMP: ' TS-TIMESTAMP                           02360000
002370     .                                                            02370000
002380 700-RESTART-CONTROL.                                             02380000
002390     MOVE CS-PROGRAM                                              02390000
002400     TO NM-ID-RS-PROGRAM OF DCLDZ01RSTV.                          02400000
002410     MOVE DA-DD-MM-CCYY                                           02410000
002420     TO DA-CR-RS         OF DCLDZ01RSTV.                          02420000
002430     MOVE 1                                                       02430000
002440     TO NB-ID-RS-PHASE   OF DCLDZ01RSTV.                          02440000
002450                                                                  02450000
002460     PERFORM 700-SELECT-DZ01RSTV.                                 02460000
002470                                                                  02470000
002480     EVALUATE SQLCODE                                             02480000
002490       WHEN 0     PERFORM 810-JOB-IS-RESTART                      02490000
002500       WHEN 100   PERFORM 820-WRITE-RESTART-REC                   02500000
002510       WHEN OTHER PERFORM SQLERROR                                02510000
002520     END-EVALUATE.                                                02520000
002530                                                                  02530000
002540     MOVE 0 TO WS-TELLER.                                         02540000
002550     .                                                            02550000
002560                                                                  02560000
002570                                                                  02570000
002580 700-SELECT-DZ01RSTV.                                             02580000
002590     EXEC SQL                                                     02590000
002600       SELECT  NM_ID_RS_PROGRAM                                   02600000
002610       , NB_ID_RS_PHASE                                           02610000
002620       , DA_CR_RS                                                 02620000
002630       , CO_ID_RS                                                 02630000
002640       , NB_DAY_RS                                                02640000
002650       , TE_CH_RS_DATA                                            02650000
002660       INTO  :DCLDZ01RSTV.NM-ID-RS-PROGRAM                        02660000
002670       , :DCLDZ01RSTV.NB-ID-RS-PHASE                              02670000
002680       , :DCLDZ01RSTV.DA-CR-RS                                    02680000
002690       , :DCLDZ01RSTV.CO-ID-RS                                    02690000
002700       , :DCLDZ01RSTV.NB-DAY-RS                                   02700000
002710       , :DCLDZ01RSTV.TE-CH-RS-DATA                               02710000
002720       FROM  DZ01RSTV                                             02720000
002730       WHERE NM_ID_RS_PROGRAM =                                   02730000
002740       :DCLDZ01RSTV.NM-ID-RS-PROGRAM                              02740000
002750       AND NB_ID_RS_PHASE = :DCLDZ01RSTV.NB-ID-RS-PHASE           02750000
002760       AND DA_CR_RS = :DCLDZ01RSTV.DA-CR-RS                       02760000
002770       QUERYNO 376                                                02770000
002780     END-EXEC                                                     02780000
002790                                                                  02790000
002800     EVALUATE SQLCODE                                             02800000
002810       WHEN 0                                                     02810000
002820            SET RESTART-FOUND TO TRUE                             02820000
002830       WHEN 100                                                   02830000
002840            SET RESTART-NOT-FOUND TO TRUE                         02840000
002850       WHEN OTHER                                                 02850000
002860            PERFORM SQLERROR                                      02860000
002870     END-EVALUATE                                                 02870000
002880     .                                                            02880000
002890                                                                  02890000
002900                                                                  02900000
002910 700-UPDATE-DZ01RSTV.                                             02910000
002920     EXEC SQL                                                     02920000
002930       UPDATE DZ01RSTV                                            02930000
002940       SET TE_CH_RS_DATA = :DCLDZ01RSTV.TE-CH-RS-DATA             02940000
002950       , CO_ID_RS = :DCLDZ01RSTV.CO-ID-RS                         02950000
002960       WHERE NM_ID_RS_PROGRAM =                                   02960000
002970       :DCLDZ01RSTV.NM-ID-RS-PROGRAM                              02970000
002980       AND NB_ID_RS_PHASE = :DCLDZ01RSTV.NB-ID-RS-PHASE           02980000
002990       AND DA_CR_RS = :DCLDZ01RSTV.DA-CR-RS                       02990000
003000       QUERYNO 398                                                03000000
003010     END-EXEC                                                     03010000
003020                                                                  03020000
003030     EVALUATE SQLCODE                                             03030000
003040       WHEN 0                                                     03040000
003050            CONTINUE                                              03050000
003060       WHEN OTHER                                                 03060000
003070            PERFORM SQLERROR                                      03070000
003080     END-EVALUATE                                                 03080000
003090     .                                                            03090000
003100                                                                  03100000
003110                                                                  03110000
003120 700-INSERT-DZ01RSTV.                                             03120000
003130     EXEC SQL                                                     03130000
003140       INSERT INTO DZ01RSTV                                       03140000
003150       (NM_ID_RS_PROGRAM                                          03150000
003160       ,NB_ID_RS_PHASE                                            03160000
003170       ,DA_CR_RS                                                  03170000
003180       ,CO_ID_RS                                                  03180000
003190       ,NB_DAY_RS                                                 03190000
003200       ,TE_CH_RS_DATA)                                            03200000
003210       VALUES                                                     03210000
003220       (:DCLDZ01RSTV.NM-ID-RS-PROGRAM                             03220000
003230       ,:DCLDZ01RSTV.NB-ID-RS-PHASE                               03230000
003240       ,:DCLDZ01RSTV.DA-CR-RS                                     03240000
003250       ,:DCLDZ01RSTV.CO-ID-RS                                     03250000
003260       ,:DCLDZ01RSTV.NB-DAY-RS                                    03260000
003270       ,:DCLDZ01RSTV.TE-CH-RS-DATA)                               03270000
003280       QUERYNO 442                                                03280000
003290     END-EXEC                                                     03290000
003300                                                                  03300000
003310     EVALUATE SQLCODE                                             03310000
003320       WHEN 0                                                     03320000
003330            CONTINUE                                              03330000
003340       WHEN OTHER                                                 03340000
003350            PERFORM SQLERROR                                      03350000
003360     END-EVALUATE                                                 03360000
003370     .                                                            03370000
003380 810-JOB-IS-RESTART.                                              03380000
003390     MOVE TE-CH-RS-DATA OF DCLDZ01RSTV TO WS-RESTART-REC.         03390000
003400                                                                  03400000
003410     IF CO-ID-RS OF DCLDZ01RSTV = '1'                             03410000
003420        THEN DISPLAY 'PREVIOUS RUN COMPLETE'                      03420000
003430        CONTINUE                                                  03430000
003440     ELSE DISPLAY 'RESUMING FROM CHECKPOINT: '                    03440000
003450        MOVE NB-READ OF WS-RESTART-REC                            03450000
003460        TO WS-NB-INPUT-REC                                        03460000
003470     END-IF.                                                      03470000
003480     .                                                            03480000
003490                                                                  03490000
003500                                                                  03500000
003510 820-WRITE-RESTART-REC.                                           03510000
003520     MOVE '0'                TO CO-ID-RS OF DCLDZ01RSTV.          03520000
003530     MOVE 7                  TO NB-DAY-RS OF DCLDZ01RSTV.         03530000
003540     MOVE 1215               TO NB-READ OF WS-RESTART-REC.        03540000
003550     MOVE ZERO               TO WS-NB-INPUT-REC.                  03550000
003560     MOVE WS-RESTART-REC                                          03560000
003570     TO TE-CH-RS-DATA OF DCLDZ01RSTV.                             03570000
003580                                                                  03580000
003590     PERFORM 700-INSERT-DZ01RSTV.                                 03590000
003600                                                                  03600000
003610     DISPLAY 'STARTING NEW RUN - RESTART RECORD CREATED'.         03610000
003620     .                                                            03620000
003630                                                                  03630000
003640                                                                  03640000
003650 800-PROCESS-COMMIT.                                              03650000
003660     IF SW-EOF = 'Y'                                              03660000
003670        THEN MOVE '1'           TO CO-ID-RS OF DCLDZ01RSTV        03670000
003680     ELSE MOVE '0'           TO CO-ID-RS OF DCLDZ01RSTV           03680000
003690     END-IF.                                                      03690000
003700                                                                  03700000
003710     MOVE WS-RESTART-REC                                          03710000
003720     TO TE-CH-RS-DATA OF DCLDZ01RSTV.                             03720000
003730                                                                  03730000
003740     PERFORM 700-UPDATE-DZ01RSTV.                                 03740000
003750                                                                  03750000
003760     EXEC SQL                                                     03760000
003770       COMMIT                                                     03770000
003780     END-EXEC.                                                    03780000
003790                                                                  03790000
003800     EVALUATE SQLCODE                                             03800000
003810       WHEN 0                                                     03810000
003820            ADD 1 TO WS-COMMIT-COUNTER                            03820000
003830       WHEN OTHER                                                 03830000
003840            PERFORM SQLERROR                                      03840000
003850     END-EVALUATE.                                                03850000
003860     .                                                            03860000
003870                                                                  03870000
003880                                                                  03880000
003890                                                                  03890000
003900 100-INITIALISATIE.                                               03900000
003910     MOVE DATE8-LS       TO DATE-DMY8.                            03910000
003920     MOVE CORR DATE-DMY8 TO DATE-DMY.                             03920000
003930     MOVE CORR DATE-DMY8 TO DATE-YMD.                             03930000
003940     MOVE CORR DATE-DMY8 TO DATE-YMD8.                            03940000
003950                                                                  03950000
003960     OPEN INPUT INFIL.                                            03960000
003970     MOVE +0 TO TELLER.                                           03970000
003980     PERFORM 900-LEES-INFIL.                                      03980000
003990                                                                  03990000
004000 110-POSITIONEREN-INFIL.                                          04000000
004010     ADD +1 TO TELLER.                                            04010000
004020     PERFORM 900-LEES-INFIL.                                      04020000
004030     IF EOF                                                       04030000
004040        PERFORM STOP01.                                           04040000
004050                                                                  04050000
004060 200-VERWERK-INFIL.                                               04060000
004070     ADD +1 TO TELLER.                                            04070000
004080     IF CO-STCIRC-OORD = '1'                                      04080000
004090        THEN PERFORM 210-STORE-EFF                                04090000
004100     ELSE PERFORM 220-MOD-EVEF                                    04100000
004110     END-IF.                                                      04110000
004120     IF TELLER NOT < +100                                         04120000
004130        PERFORM 800-TEST-FFRECAB                                  04130000
004140        MOVE 'COMMIT' TO SQL-LOCATION.                            04140000
004150        EXEC SQL                                                  04150000
004160          COMMIT                                                  04160000
004170        END-EXEC.                                                 04170000
004180        MOVE +0 TO TELLER.                                        04180000
004190        PERFORM 900-LEES-INFIL.                                   04190000
004200                                                                  04200000
004210 210-STORE-EFF.                                                   04210000
004220 VMBEVEF.                                                         04220000
004230     MOVE '1002' TO CT-RKTPROD-479BEFF OF DCLDZBEFFTV             04230000
004240     MOVE NR-ST-FORM-AS OF VMDZ205I TO NR-ID-STOCK-CD OF VMBEFF.  04240000
004250     MOVE NS-DB-STOCK-FORM-AS TO NS-DBSTK-479BEFF OF DCLDZBEFFTV. 04250000
004260     MOVE NR-ID-040SECU TO CO-IDPRKSK-479BEFF OF DCLDZBEFFTV.     04260000
004270     MOVE NS-SEQ-040IRMO TO NS-IRMOSTK-479BEFF OF DCLDZBEFFTV.    04270000
004280     MOVE DA-UB-FORM-AS OF VMDZ205I TO DA-UBSECIS-479BEFF         04280000
004290     OF DCLDZBEFFTV.                                              04290000
004300     MOVE 0 TO NR-IDISSUE-479BEFF OF DCLDZBEFFTV                  04300000
004310     NR-CDISSUE-479BEFF                                           04310000
004320     OF DCLDZBEFFTV.                                              04320000
004330     MOVE DATE-YMD8 TO DA-CREVTPD-479EVEF OF DCLDZEVEFTV.         04330000
004340     MOVE '0168' TO CT-RKTEVPR-479EVEF OF DCLDZEVEFTV.            04340000
004350     MOVE '0219' TO CT-RKTGDSV-479EVEF OF DCLDZEVEFTV.            04350000
004360     MOVE NR-CIO-FORM-AS-R          TO HULP-NR-CIO.               04360000
004370     MOVE DA-CREA-FORM-AS-R         TO HULP-DA-CREA.              04370000
004380     MOVE NR-ID-FORM-AS OF VMDZ205I TO HULP-NR-ID.                04380000
004390     MOVE CT-OPD-FORM-AS-R          TO HULP-CT-OPD.               04390000
004400     MOVE CT-OPG-FORM-AS-R          TO HULP-CT-OPG.               04400000
004410     MOVE HULP-NR-ID-GOOD TO NR-IDGOOD-479EVEF OF DCLDZEVEFTV.    04410000
004420     MOVE NR-CIO-FORM-AS OF VMDZ205I TO DB-NR-CI.                 04420000
004430                                                                  04430000
004440*                                                                 04440000
004450* STOCKEREN VAN DE RECORDS :                                      04450000
004460*    - VMBWCEF                                                    04460000
004470     MOVE NR-CIO-FORM-AS OF VMDZ205I TO NR-CI OF VMBEVEF.         04470000
004480*DB2-KEEP: VMBTL07-R01 has no usable DB2 column mapping - map this04480000
004490*IDMS logic manually.                                             04490000
004500*DB2-KEEP   STORE VMBTL07-R01 WHERE ST-VMBEVEF.                   04500000
004510*=                                                                04510000
004520*=      OBTAIN VMBEFF                                             04520000
004530*=          WHERE CALCKEY EQ KY-EFFECT OF VMBEFF OF LR            04530000
004540*=          ON 0326 RETURN VMBEFF-NOT-FND                         04540000
004550*DB2: INSERT conversion skipped for VMBEVEF.                      04550000
004560*DB2: missing insert columns.                                     04560000
004570     CONTINUE.                                                    04570000
004580*=                                                                04580000
004590     IF SQLCODE = 100 OR 'LR-ERROR'                               04590000
004600        PERFORM IDMS-STOP.                                        04600000
004610                                                                  04610000
004620 220-MOD-EVEF.                                                    04620000
004630     MOVE '1002' TO CT-RKTPROD-479BEFF OF DCLDZBEFFTV.            04630000
004640     MOVE NR-ST-FORM-AS   OF VMDZ205I  TO NR-ID-STOCK-CD.         04640000
004650     MOVE NS-DB-STOCK-FORM-AS TO NS-DBSTK-479BEFF OF DCLDZBEFFTV. 04650000
004660*                                                                 04660000
004670*DB2: Expanded LRF FIRST VMBTL07-R01 WHERE ALL-VMBEVEF-BY-VMBEFF  04670000
004680*  -> VMBEVEF WITHIN VMBEFF-VMBEVEF.                              04680000
004690*DB2: LRF ALL-VMBEVEF-BY-VMBEFF extra filter: CT-RK-TEVPR = '0168'04690000
004700*  AND CT-RK-TGDSV = '0219' - add to the generated cursor WHERE.  04700000
004710*DB2: Converted OBTAIN FIRST VMBEVEF WITHIN VMBEFF-VMBEVEF.       04710000
004720     PERFORM 710-OPEN-DZEVEFC1.                                   04720000
004730     PERFORM 720-FETCH-DZEVEFC1 UNTIL DZEVEFC1-EOC.               04730000
004740     PERFORM 730-CLOSE-DZEVEFC1.                                  04740000
004750     IF NOT SQLCODE = 100                                         04750000
004760        DISPLAY ' ** VM1BD526 RECH EVTS SOUSCRIPTION **'          04760000
004770        DISPLAY 'NR-ST:' NR-ST-FORM-AS OF VMDZ205I                04770000
004780        ' NS-DB:' NS-DB-STOCK-FORM-AS OF VMDZ205I                 04780000
004790        ' LR-STATUS:' LR-STATUS                                   04790000
004800        CALL USERABEN                                             04800000
004810     END-IF.                                                      04810000
004820                                                                  04820000
004830     MOVE NR-CIO-FORM-AS-R             TO HULP-NR-CIO.            04830000
004840     MOVE DA-CREA-FORM-AS-R            TO HULP-DA-CREA.           04840000
004850     MOVE NR-ID-FORM-AS OF VMDZ205I    TO HULP-NR-ID.             04850000
004860     MOVE CT-OPD-FORM-AS-R             TO HULP-CT-OPD.            04860000
004870     MOVE CT-OPG-FORM-AS-R             TO HULP-CT-OPG.            04870000
004880     MOVE HULP-NR-ID-GOOD TO NR-IDGOOD-479EVEF OF DCLDZEVEFTV.    04880000
004890                                                                  04890000
004900*DB2-KEEP: VMBTL07-R01 has no usable DB2 column mapping - map this04900000
004910*IDMS logic manually.                                             04910000
004920*DB2-KEEP   MODIFY VMBTL07-R01 WHERE MO-VMBEVEF.                  04920000
004930     IF NOT SQLCODE = 100                                         04930000
004940 048410        DISPLAY ' ** VM1BD526 UPDATE CLÉ FORM **'          04940000
004950        DISPLAY 'NR-ST:' NR-ST-FORM-AS OF VMDZ205I                04950000
004960        ' NS-DB:' NS-DB-STOCK-FORM-AS OF VMDZ205I                 04960000
004970        ' LR-STATUS:' LR-STATUS                                   04970000
004980        CALL USERABEN                                             04980000
004990     END-IF.                                                      04990000
005000                                                                  05000000
005010 800-TEST-FFRECAB.                                                05010000
005020                                                                  05020000
005030 900-LEES-INFIL.                                                  05030000
005040     READ INFIL                                                   05040000
005050        AT END MOVE +1 TO SW-EOF.                                 05050000
005060                                                                  05060000
005070 STOP01.                                                          05070000
005080     DISPLAY '##&&VM1BD526 - STOP01 : TE WEINIG REC OP INFIL'.    05080000
005090     CALL USERABEN.                                               05090000
005100                                                                  05100000
005110 IDMS-STOP.                                                       05110000
005120     DISPLAY '##&&LR-STATUS    : ', LR-STATUS.                    05120000
005130     DISPLAY '##&&ERROR-STATUS : ', ERROR-STATUS.                 05130000
005140     DISPLAY '##&&DML-SEQUENCE : ', DML-SEQUENCE.                 05140000
005150     ROLLBACK.                                                    05150000
005160     CALL USERABEN.                                               05160000
005170                                                                  05170000
005180                                                                  05180000
005190                                                                  05190000
005200*DB2 GENERATED CURSOR OPEN FETCH CLOSE PARAGRAPHS              *  05200000
005210                                                                  05210000
005220 710-OPEN-DZEVEFC1.                                               05220000
005230D    DISPLAY '710-OPEN-DZEVEFC1.'                                 05230000
005240     MOVE 710    TO SQL-LOCATION                                  05240000
005250                                                                  05250000
005260     EXEC SQL                                                     05260000
005270       OPEN DZEVEFC1                                              05270000
005280     END-EXEC                                                     05280000
005290                                                                  05290000
005300     EVALUATE SQLCODE                                             05300000
005310       WHEN ZERO                                                  05310000
005320            SET DZEVEFC1-NOT-EOC TO TRUE                          05320000
005330       WHEN OTHER                                                 05330000
005340            MOVE 710    TO SQL-LOCATION                           05340000
005350            DISPLAY 'ERROR WHILE OPENING CURSOR DZEVEFC1'         05350000
005360            PERFORM SQLERROR                                      05360000
005370     END-EVALUATE                                                 05370000
005380     .                                                            05380000
005390                                                                  05390000
005400 720-FETCH-DZEVEFC1.                                              05400000
005410D    DISPLAY '720-FETCH-DZEVEFC1.'                                05410000
005420     SET DZEVEFC1-NOT-EOC TO TRUE                                 05420000
005430     MOVE 720    TO SQL-LOCATION                                  05430000
005440                                                                  05440000
005450     EXEC SQL                                                     05450000
005460       FETCH DZEVEFC1                                             05460000
005470       INTO :DCLDZEVEFTV.CT-RKTEVPR-479EVEF                       05470000
005480       , :DCLDZEVEFTV.CT-RKTGDSV-479EVEF                          05480000
005490       , :DCLDZEVEFTV.DA-CREVTPD-479EVEF                          05490000
005500       , :DCLDZEVEFTV.NR-IDGOOD-479EVEF                           05500000
005510       , :DCLDZEVEFTV.NR-ID-479EVEF                               05510000
005520     END-EXEC                                                     05520000
005530                                                                  05530000
005540     EVALUATE SQLCODE                                             05540000
005550       WHEN ZERO                                                  05550000
005560            ADD 1 TO WS-NB-EVEF-COUNT                             05560000
005570            CONTINUE                                              05570000
005580       WHEN 100                                                   05580000
005590            SET DZEVEFC1-EOC TO TRUE                              05590000
005600       WHEN OTHER                                                 05600000
005610            MOVE 720    TO SQL-LOCATION                           05610000
005620            DISPLAY 'ERROR WHILE FETCHING CURSOR DZEVEFC1'        05620000
005630            DISPLAY 'CT-RKTEVPR-479EVEF : ' CT-RKTEVPR-479EVEF    05630000
005640            OF DCLDZEVEFTV                                        05640000
005650            DISPLAY 'CT-RKTGDSV-479EVEF : ' CT-RKTGDSV-479EVEF    05650000
005660            OF DCLDZEVEFTV                                        05660000
005670            DISPLAY 'DA-CREVTPD-479EVEF : ' DA-CREVTPD-479EVEF    05670000
005680            OF DCLDZEVEFTV                                        05680000
005690            DISPLAY 'NR-IDGOOD-479EVEF  : ' NR-IDGOOD-479EVEF     05690000
005700            OF DCLDZEVEFTV                                        05700000
005710            DISPLAY 'NR-ID-479EVEF      : ' NR-ID-479EVEF         05710000
005720            OF DCLDZEVEFTV                                        05720000
005730            PERFORM SQLERROR                                      05730000
005740     END-EVALUATE                                                 05740000
005750     .                                                            05750000
005760                                                                  05760000
005770 730-CLOSE-DZEVEFC1.                                              05770000
005780D    DISPLAY '730-CLOSE-DZEVEFC1.'                                05780000
005790     MOVE 730    TO SQL-LOCATION                                  05790000
005800                                                                  05800000
005810     EXEC SQL                                                     05810000
005820       CLOSE DZEVEFC1                                             05820000
005830     END-EXEC                                                     05830000
005840                                                                  05840000
005850     EVALUATE SQLCODE                                             05850000
005860       WHEN ZERO                                                  05860000
005870            CONTINUE                                              05870000
005880       WHEN OTHER                                                 05880000
005890            MOVE 730    TO SQL-LOCATION                           05890000
005900            DISPLAY 'ERROR WHILE CLOSING CURSOR DZEVEFC1'         05900000
005910            PERFORM SQLERROR                                      05910000
005920     END-EVALUATE                                                 05920000
005930     .                                                            05930000
005940                                                                  05940000
005950*SQLERROR ROUTINE.                                                05950000
005960     EXEC SQL                                                     05960000
005970       INCLUDE SQLERROR                                           05970000
005980     END-EXEC.                                                    05980000
