000100 CBL ARITH(EXTEND)                                                00010000
000200 IDENTIFICATION DIVISION.                                         00020000
000300*-----------------------.                                         00030000
000400 PROGRAM-ID.    VMDZ1567.                                         00040000
000500 AUTHOR.        VINAY MAHAJAN.                                    00050000
000600 DATE-WRITTEN.  FEB 2026.                                         00060000
000700 DATE-COMPILED.                                                   00070000
000800                                                                  00080000
000900****************************************************************  00090000
001000*REMARKS.       AANDUIDEN BOEKING IN DB FORMULIER              *  00100000
001100*               VOOR EFFECTENDOSSIERS.                         *  00110000
001200*                                                              *  00120000
001300*  THIS PROGRAM IS BEING USED TO UPDATE WITH THE INPUT KASBONS *  00130000
001400*  DATA (ESPECIALLY ON DATE OF ACCOUNTING REFUNDS FIELD DATA), *  00140000
001500*  IN THE FOLLOWING (1) KASBONS DB2 TABLE: DZBFARTB            *  00150000
001600*                                                              *  00160000
001700*  DZSIARTV (PARENT) ---> DZBFARTV(CHILD)                      *  00170000
001800*                                                              *  00180000
001900*  AND ALSO UPDATE THE DATA (BOTH INSERT & UPDATE) IN THE      *  00190000
002000*  KASBONS DB2 RESTART TABLE: DZ01RSTB.                        *  00200000
002100*                                                              *  00210000
002200****************************************************************  00220000
002300                                                                  00230000
002400 ENVIRONMENT DIVISION.                                            00240000
002500*--------------------.                                            00250000
002600 CONFIGURATION SECTION.                                           00260000
002700 SPECIAL-NAMES.                                                   00270000
002800     DECIMAL-POINT IS COMMA.                                      00280000
002900                                                                  00290000
003000 INPUT-OUTPUT SECTION.                                            00300000
003100 FILE-CONTROL.                                                    00310000
003200     SELECT OPERATIES ASSIGN TO UT-S-DD010.                       00320000
003300                                                                  00330000
003400 DATA DIVISION.                                                   00340000
003500*-------------.                                                   00350000
003600 FILE SECTION.                                                    00360000
003700 FD   OPERATIES                                                   00370000
003800      BLOCK CONTAINS 0 RECORDS                                    00380000
003900      RECORD CONTAINS 1200 CHARACTERS                             00390000
004000      RECORDING F                                                 00400000
004100      LABEL RECORDS STANDARD.                                     00410000
004200 01   OPERATIES-REC             PIC X(1200).                      00420000
004300                                                                  00430000
004400 WORKING-STORAGE SECTION.                                         00440000
004500 77  USERABEN                   PIC X(8) VALUE 'USERABEN'.        00450000
004600 77  CS-PROGRAM                 PIC X(8) VALUE 'VMDZ1567'.        00460000
004700                                                                  00470000
004800 01 WS-SWITCHES.                                                  00480000
004900     02  SW-VMDZ205I            PIC X.                            00490000
005000         88  VMDZ205I-NOT-EOF   VALUE 'N'.                        00500000
005100         88  VMDZ205I-EOF       VALUE 'Y'.                        00510000
005200                                                                  00520000
005300 01  HELP-VARIABLE.                                               00530000
005400     02  WS-RESTART-REC.                                          00540000
005500         03  NB-READ            PIC 9(15).                        00550000
005600         03  KY-RESTART         PIC X(1200).                      00560000
005700                                                                  00570000
005800     02  WS-INPUT-KASBONS       PIC X(1200).                      00580000
005900     02  WS-TELLER              PIC 9(9)   COMP-3 VALUE ZERO.     00590000
006000     02  WS-NB-INPUT-UPD-I      PIC 9(7)   COMP-3 VALUE ZERO.     00600000
006100     02  WS-NB-BFAR-UPD-I       PIC S9(11) COMP-3 VALUE +0.       00610000
006200                                                                  00620000
006300 01  STOP-DATONLY.                                                00630000
006400     02  DATE-YMD.                                                00640000
006500         03  D-YEAR             PIC 99.                           00650000
006600         03  D-MONTH            PIC 99.                           00660000
006700         03  D-DAY              PIC 99.                           00670000
006800     02  DATE-DMY.                                                00680000
006900         03  D-DAY              PIC 99.                           00690000
007000         03  D-MONTH            PIC 99.                           00700000
007100         03  D-YEAR             PIC 99.                           00710000
007200     02  DATE-YMD8.                                               00720000
007300         03  D-CENT             PIC 99.                           00730000
007400         03  D-YEAR             PIC 99.                           00740000
007500         03  D-MONTH            PIC 99.                           00750000
007600         03  D-DAY              PIC 99.                           00760000
007700     02  DATE-DMY8.                                               00770000
007800         03  D-DAY              PIC 99.                           00780000
007900         03  D-MONTH            PIC 99.                           00790000
008000         03  D-CENT             PIC 99.                           00800000
008100         03  D-YEAR             PIC 99.                           00810000
008200                                                                  00820000
008300*                                                                 00830000
008400 01  WS-DATUMVELDEN.                                              00840000
008500     03  DA-YYMMDD.                                               00850000
008600         05  YY                 PIC 99            VALUE ZERO.     00860000
008700         05  MM                 PIC 99            VALUE ZERO.     00870000
008800         05  DD                 PIC 99            VALUE ZERO.     00880000
008900     03  DA-DDMMCCYY.                                             00890000
009000         05  DD                 PIC 99            VALUE ZERO.     00900000
009100         05  MM                 PIC 99            VALUE ZERO.     00910000
009200         05  CC                 PIC 99            VALUE ZERO.     00920000
009300         05  YY                 PIC 99            VALUE ZERO.     00930000
009400     03  DA-CCYYMMDD.                                             00940000
009500         05  CC                 PIC 99            VALUE ZERO.     00950000
009600         05  YY                 PIC 99            VALUE ZERO.     00960000
009700         05  MM                 PIC 99            VALUE ZERO.     00970000
009800         05  DD                 PIC 99            VALUE ZERO.     00980000
009900     03  DA-CCYYMMDD-R REDEFINES DA-CCYYMMDD.                     00990000
010000         05  CCYY               PIC 9999.                         01000000
010100         05  MM                 PIC 99.                           01010000
010200         05  DD                 PIC 99.                           01020000
010300     02  DA-DD-MM-CCYY.                                           01030000
010400         03  DD                 PIC 9(02).                        01040000
010500         03  TE-MARKER5         PIC X             VALUE '.'.      01050000
010600         03  MM                 PIC 9(02).                        01060000
010700         03  TE-MARKER6         PIC X             VALUE '.'.      01070000
010800         03  CCYY               PIC 9(04).                        01080000
010900                                                                  01090000
011000* -----------------------------                                   01100000
011100 01  WS-TIMESTAMP-FIELDS.                                         01110000
011200     05 TS-SYSTEM.                                                01120000
011300        10  DA-SYS.                                               01130000
011400            15  DA-SYS-CCYY.                                      01140000
011500                20  CC          PIC X(2).                         01150000
011600                20  YY          PIC X(2).                         01160000
011700            15  MM              PIC X(2).                         01170000
011800            15  DD              PIC X(2).                         01180000
011900        10  HR-SYS.                                               01190000
012000            15  HH              PIC X(2).                         01200000
012100            15  MI              PIC X(2).                         01210000
012200            15  SS              PIC X(2).                         01220000
012300            15  TT              PIC X(2).                         01230000
012400     05 TS-TIMESTAMP.                                             01240000
012500        10  CC                  PIC X(2).                         01250000
012600        10  YY                  PIC X(2).                         01260000
012700        10  TE-MARKER1          PIC X             VALUE '-'.      01270000
012800        10  MM                  PIC X(2).                         01280000
012900        10  TE-MARKER2          PIC X             VALUE '-'.      01290000
013000        10  DD                  PIC X(2).                         01300000
013100        10  TE-MARKER3          PIC X             VALUE '-'.      01310000
013200        10  HH                  PIC X(2).                         01320000
013300        10  TE-MARKER4          PIC X             VALUE '.'.      01330000
013400        10  MI                  PIC X(2).                         01340000
013500        10  TE-MARKER5          PIC X             VALUE '.'.      01350000
013600        10  SS                  PIC X(2).                         01360000
013700        10  TE-MARKER6          PIC X             VALUE '.'.      01370000
013800        10  TT                  PIC X(2).                         01380000
013900        10  NNNN                PIC 9(04)         VALUE 0.        01390000
014000                                                                  01400000
014100                                                                  01410000
014200*----- INCLUDE FOR DB2 ------------------------------------------*01420000
014300     EXEC SQL INCLUDE SQLERRWS END-EXEC.                          01430000
014400     EXEC SQL INCLUDE SQLCA    END-EXEC.                          01440000
014500                                                                  01450000
014600*----- INCLUDE VIEWS --------------------------------------------*01460000
014700     EXEC SQL INCLUDE DZBFARTV END-EXEC.                          01470000
014800     EXEC SQL INCLUDE DZ01RSTV END-EXEC.                          01480000
014900*                                                                 01490000
015000 COPY VMDZ205I.                                                   01500000
015100                                                                  01510000
015200 LINKAGE SECTION.                                                 01520000
015300 01  PARAM-DATONLY.                                               01530000
015400     03  L-PARAM                PIC S9(4) COMP.                   01540000
015500     03  DATUMLS.                                                 01550000
015600         05  DATE-IND           PIC X.                            01560000
015700         05  DATE8-LS           PIC X(8).                         01570000
015800                                                                  01580000
015900 PROCEDURE DIVISION USING PARAM-DATONLY.                          01590000
016000*--------------------------------------.                          01600000
016100*                                                                 01610000
016200     PERFORM     820000-GET-TIMESTAMP.                            01620000
016300     SET         VMDZ205I-NOT-EOF          TO TRUE.               01630000
016400     INITIALIZE  HELP-VARIABLE.                                   01640000
016500                                                                  01650000
016600     MOVE DATE8-LS                         TO DATE-DMY8.          01660000
016700     MOVE CORR DATE-DMY8                   TO DATE-YMD.           01670000
016800     MOVE CORR DATE-DMY8                   TO DATE-DMY.           01680000
016900     MOVE CORR DATE-DMY8                   TO DATE-YMD8.          01690000
017000                                                                  01700000
017100     MOVE ZEROES                           TO DA-CCYYMMDD.        01710000
017200     MOVE DATE-YMD8                        TO DA-CCYYMMDD.        01720000
017300     MOVE CORR DA-CCYYMMDD-R               TO DA-DD-MM-CCYY.      01730000
017400                                                                  01740000
017500     MOVE 'VMDZ1567' TO PROGRAM-NAME.                             01750000
017600     OPEN INPUT OPERATIES.                                        01760000
017700*                                                                 01770000
017800     PERFORM 700-RESTART-CONTROL.                                 01780000
017900                                                                  01790000
018000     PERFORM READ-FLAT-FILE.                                      01800000
018100                                                                  01810000
018200     PERFORM 1000-VERWERKING UNTIL VMDZ205I-EOF.                  01820000
018300                                                                  01830000
018400     PERFORM 800-PROCESS-COMMIT.                                  01840000
018500                                                                  01850000
018600     DISPLAY 'NUMBER OF RECORDS PROCESSED: ' WS-NB-INPUT-UPD-I.   01860000
018700     DISPLAY 'NUMBER OF UPDATE BFAR      : ' WS-NB-BFAR-UPD-I.    01870000
018800     CLOSE OPERATIES.                                             01880000
018900     STOP RUN.                                                    01890000
019000                                                                  01900000
019100                                                                  01910000
019200 1000-VERWERKING.                                                 01920000
019300*-----------                                                      01930000
019400     INITIALIZE DCLDZBFARTV.                                      01940000
019500                                                                  01950000
019600     MOVE '1815'                           TO CT-TGDSERV-479BFAR  01960000
019700                                           OF DCLDZBFARTV.        01970000
019800     MOVE NR-CIO-FORM-AS-R                 TO NR-CIOFMAS-479BFAR  01980000
019900                                           OF DCLDZBFARTV.        01990000
020000                                                                  02000000
020100     MOVE ZEROES                           TO DA-CCYYMMDD.        02010000
020200     MOVE DA-CREA-FORM-AS-R                TO DA-CCYYMMDD.        02020000
020300     IF   DA-CCYYMMDD = ZERO OR DA-CCYYMMDD = SPACES              02030000
020400          MOVE 00010101                    TO DA-CCYYMMDD.        02040000
020500     MOVE CORR DA-CCYYMMDD-R               TO DA-DD-MM-CCYY.      02050000
020600     MOVE DA-DD-MM-CCYY                    TO DA-CRFMAS-479BFAR   02060000
020700                                           OF DCLDZBFARTV.        02070000
020800                                                                  02080000
020900     MOVE NR-ID-FORM-AS OF VMDZ205I        TO NR-IDFMAS-479BFAR   02090000
021000                                           OF DCLDZBFARTV.        02100000
021100     MOVE CT-OPG-FORM-AS-R                 TO CT-OPGFMAS-479BFAR  02110000
021200                                           OF DCLDZBFARTV.        02120000
021300     MOVE CT-OPD-FORM-AS-R                 TO CT-OPDFMAS-479BFAR  02130000
021400                                           OF DCLDZBFARTV.        02140000
021500                                                                  02150000
021600     MOVE ZEROES                           TO DA-CCYYMMDD.        02160000
021700     MOVE DATE-YMD8                        TO DA-CCYYMMDD.        02170000
021800     MOVE CORR DA-CCYYMMDD-R               TO DA-DD-MM-CCYY.      02180000
021900     MOVE DA-DD-MM-CCYY                    TO DA-INFSDGD-479BFAR  02190000
022000                                           OF DCLDZBFARTV.        02200000
022100                                                                  02210000
022200     MOVE TS-TIMESTAMP                     TO TS-UPDATE-479BFAR   02220000
022300                                           OF DCLDZBFARTV.        02230000
022400                                                                  02240000
022500     MOVE CS-PROGRAM                       TO ID-USERID-479BFAR   02250000
022600                                           OF DCLDZBFARTV.        02260000
022700                                                                  02270000
022800     PERFORM 1100-UPDATE-VMBFAR.                                  02280000
022900                                                                  02290000
023000     IF WS-TELLER > 99                                            02300000
023100        PERFORM 800-PROCESS-COMMIT                                02310000
023200     END-IF.                                                      02320000
023300                                                                  02330000
023400     PERFORM READ-FLAT-FILE.                                      02340000
023500                                                                  02350000
023600                                                                  02360000
023700                                                                  02370000
023800 READ-FLAT-FILE.                                                  02380000
023900                                                                  02390000
024000     INITIALIZE VMDZ205I.                                         02400000
024100                                                                  02410000
024200     READ OPERATIES INTO VMDZ205I                                 02420000
024300          AT END SET VMDZ205I-EOF          TO TRUE.               02430000
024400                                                                  02440000
024500     IF VMDZ205I-NOT-EOF                                          02450000
024600     THEN                                                         02460000
024700          ADD +1 TO WS-TELLER                                     02470000
024800          ADD +1 TO WS-NB-INPUT-UPD-I                             02480000
024900          MOVE VMDZ205I TO WS-INPUT-KASBONS                       02490000
025000     END-IF.                                                      02500000
025100                                                                  02510000
025200                                                                  02520000
025300                                                                  02530000
025400 820000-GET-TIMESTAMP.                                            02540000
025500D    DISPLAY '820000-GET-TIMESTAMP'.                              02550000
025600     MOVE FUNCTION CURRENT-DATE            TO TS-SYSTEM.          02560000
025700     MOVE CC OF TS-SYSTEM                  TO CC OF TS-TIMESTAMP  02570000
025800     MOVE YY OF TS-SYSTEM                  TO YY OF TS-TIMESTAMP  02580000
025900     MOVE MM OF TS-SYSTEM                  TO MM OF TS-TIMESTAMP  02590000
026000     MOVE DD OF TS-SYSTEM                  TO DD OF TS-TIMESTAMP  02600000
026100     MOVE HH OF TS-SYSTEM                  TO HH OF TS-TIMESTAMP  02610000
026200     MOVE MI OF TS-SYSTEM                  TO MI OF TS-TIMESTAMP  02620000
026300     MOVE SS OF TS-SYSTEM                  TO SS OF TS-TIMESTAMP  02630000
026400     MOVE TT OF TS-SYSTEM                  TO TT OF TS-TIMESTAMP  02640000
026500     DISPLAY 'TIMESTAMP: ' TS-TIMESTAMP                           02650000
026600     .                                                            02660000
026700                                                                  02670000
026800                                                                  02680000
026900 700-RESTART-CONTROL.                                             02690000
027000     MOVE CS-PROGRAM    TO NM-ID-RS-PROGRAM OF DCLDZ01RSTV.       02700000
027100     MOVE DA-DD-MM-CCYY TO DA-CR-RS         OF DCLDZ01RSTV.       02710000
027200     MOVE 1             TO NB-ID-RS-PHASE   OF DCLDZ01RSTV.       02720000
027300                                                                  02730000
027400     PERFORM 700-SELECT-DZ01RSTV.                                 02740000
027500                                                                  02750000
027600     EVALUATE SQLCODE                                             02760000
027700         WHEN 0     PERFORM 710-JOB-IS-RESTART                    02770000
027800         WHEN 100   PERFORM 720-WRITE-RESTART-REC                 02780000
027900         WHEN OTHER PERFORM SQLERROR                              02790000
028000     END-EVALUATE                                                 02800000
028100     .                                                            02810000
028200                                                                  02820000
028300     MOVE 0 TO WS-TELLER.                                         02830000
028400*    SET VMDZ205I-EOF TO TRUE.                                    02840000
028500                                                                  02850000
028600                                                                  02860000
028700 710-JOB-IS-RESTART.                                              02870000
028800*    RESTART RECORD FOUND. THEREFORE RESTART PERFORMED            02880000
028900D    DISPLAY '810-JOB-IS-RESTART'                                 02890000
029000     MOVE TE-CH-RS-DATA-TEXT  TO WS-RESTART-REC                   02900000
029100                                                                  02910000
029200*    IF PREVIOUS VERSION COMPLETE -> THEN WE CAN STOP.            02920000
029300     IF CO-ID-RS IN DCLDZ01RSTV = '1'                             02930000
029400     THEN DISPLAY ' PREVIOUS RUN COMPLETE '                       02940000
029500          PERFORM 810000-CALL-USERABEN                            02950000
029600                                                                  02960000
029700     ELSE PERFORM NB-READ OF WS-RESTART-REC TIMES                 02970000
029800             PERFORM READ-FLAT-FILE                               02980000
029900             MOVE NB-READ OF WS-RESTART-REC TO WS-NB-INPUT-UPD-I  02990000
030000          END-PERFORM                                             03000000
030100                                                                  03010000
030200     END-IF                                                       03020000
030300     .                                                            03030000
030400                                                                  03040000
030500                                                                  03050000
030600 720-WRITE-RESTART-REC.                                           03060000
030700*    RESTART RECORD NOT FOUND => 1ST RUN                          03070000
030800D    DISPLAY '  820-WRITE-RESTART-REC'                            03080000
030900     MOVE '0'                TO CO-ID-RS           IN DCLDZ01RSTV 03090000
031000     MOVE 7                  TO NB-DAY-RS          IN DCLDZ01RSTV 03100000
031100     MOVE 1215               TO TE-CH-RS-DATA-LEN  IN DCLDZ01RSTV 03110000
031200     MOVE 0                  TO WS-NB-INPUT-UPD-I                 03120000
031300     MOVE WS-NB-INPUT-UPD-I  TO NB-READ OF WS-RESTART-REC         03130000
031400     INITIALIZE  KY-RESTART                                       03140000
031500     MOVE WS-RESTART-REC     TO TE-CH-RS-DATA-TEXT IN DCLDZ01RSTV 03150000
031600                                                                  03160000
031700     PERFORM 700-INSERT-DZ01RSTV                                  03170000
031800     .                                                            03180000
031900*                                                                 03190000
032000 810000-CALL-USERABEN.                                            03200000
032100D    DISPLAY '810000-CALL-USERABEN'.                              03210000
032200     CALL USERABEN.                                               03220000
032300                                                                  03230000
032400*                                                                 03240000
032500 800-PROCESS-COMMIT.                                              03250000
032600D    DISPLAY '800-PROCESS-COMMIT'.                                03260000
032700                                                                  03270000
032800     MOVE 0                  TO WS-TELLER.                        03280000
032900     MOVE WS-NB-INPUT-UPD-I  TO NB-READ.                          03290000
033000     MOVE WS-INPUT-KASBONS   TO KY-RESTART.                       03300000
033100     IF   VMDZ205I-EOF                                            03310000
033200     THEN MOVE '1'           TO CO-ID-RS  OF DCLDZ01RSTV          03320000
033300     ELSE MOVE '0'           TO CO-ID-RS  OF DCLDZ01RSTV          03330000
033400     END-IF.                                                      03340000
033500     MOVE 15                 TO TE-CH-RS-DATA-LEN.                03350000
033600     MOVE WS-RESTART-REC     TO TE-CH-RS-DATA-TEXT.               03360000
033700                                                                  03370000
033800     PERFORM 700-UPDATE-DZ01RSTV.                                 03380000
033900                                                                  03390000
034000     EXEC SQL                                                     03400000
034100          COMMIT                                                  03410000
034200     END-EXEC.                                                    03420000
034300     EVALUATE SQLCODE                                             03430000
034400        WHEN 0                                                    03440000
034500             CONTINUE                                             03450000
034600        WHEN OTHER                                                03460000
034700             DISPLAY 'ERROR REC NUMBER : ' WS-NB-INPUT-UPD-I      03470000
034800             PERFORM SQLERROR                                     03480000
034900     END-EVALUATE                                                 03490000
035000     .                                                            03500000
035100                                                                  03510000
035200*-----------------------------------------------------------      03520000
035300*                    DB2 SQL CODING                               03530000
035400*-----------------------------------------------------------      03540000
035500                                                                  03550000
035600 700-SELECT-DZ01RSTV.                                             03560000
035700                                                                  03570000
035800D    DISPLAY '700-SELECT-DZ01RSTV'                                03580000
035900     EXEC SQL                                                     03590000
036000          SELECT NM_ID_RS_PROGRAM                                 03600000
036100               , NB_ID_RS_PHASE                                   03610000
036200               , DA_CR_RS                                         03620000
036300               , CO_ID_RS                                         03630000
036400               , NB_DAY_RS                                        03640000
036500               , TE_CH_RS_DATA                                    03650000
036600            INTO :DCLDZ01RSTV.NM-ID-RS-PROGRAM                    03660000
036700               , :DCLDZ01RSTV.NB-ID-RS-PHASE                      03670000
036800               , :DCLDZ01RSTV.DA-CR-RS                            03680000
036900               , :DCLDZ01RSTV.CO-ID-RS                            03690000
037000               , :DCLDZ01RSTV.NB-DAY-RS                           03700000
037100               , :DCLDZ01RSTV.TE-CH-RS-DATA                       03710000
037200            FROM DZ01RSTV                                         03720000
037300           WHERE NM_ID_RS_PROGRAM = :DCLDZ01RSTV.NM-ID-RS-PROGRAM 03730000
037400             AND NB_ID_RS_PHASE   = :DCLDZ01RSTV.NB-ID-RS-PHASE   03740000
037500             AND DA_CR_RS         = :DCLDZ01RSTV.DA-CR-RS         03750000
037600          QUERYNO 376                                             03760000
037700     END-EXEC                                                     03770000
037800                                                                  03780000
037900     EVALUATE SQLCODE                                             03790000
038000         WHEN 0                                                   03800000
038100         WHEN 100                                                 03810000
038200              CONTINUE                                            03820000
038300         WHEN OTHER                                               03830000
038400              DISPLAY 'ERROR REC NUMBER : ' WS-NB-INPUT-UPD-I     03840000
038500              PERFORM SQLERROR                                    03850000
038600     END-EVALUATE                                                 03860000
038700     .                                                            03870000
038800                                                                  03880000
038900 700-UPDATE-DZ01RSTV.                                             03890000
039000D    DISPLAY '700-UPDATE-DZ01RSTV.'                               03900000
039100     EXEC SQL                                                     03910000
039200          UPDATE DZ01RSTV                                         03920000
039300             SET TE_CH_RS_DATA    = :DCLDZ01RSTV.TE-CH-RS-DATA    03930000
039400               , CO_ID_RS         = :DCLDZ01RSTV.CO-ID-RS         03940000
039500           WHERE NM_ID_RS_PROGRAM = :DCLDZ01RSTV.NM-ID-RS-PROGRAM 03950000
039600             AND NB_ID_RS_PHASE   = :DCLDZ01RSTV.NB-ID-RS-PHASE   03960000
039700             AND DA_CR_RS         = :DCLDZ01RSTV.DA-CR-RS         03970000
039800          QUERYNO 398                                             03980000
039900     END-EXEC                                                     03990000
040000                                                                  04000000
040100     EVALUATE SQLCODE                                             04010000
040200         WHEN 0                                                   04020000
040300              CONTINUE                                            04030000
040400         WHEN OTHER                                               04040000
040500              DISPLAY 'ERROR REC NUMBER : ' WS-NB-INPUT-UPD-I     04050000
040600              PERFORM SQLERROR                                    04060000
040700     END-EVALUATE                                                 04070000
040800     .                                                            04080000
040900                                                                  04090000
041000 700-INSERT-DZ01RSTV.                                             04100000
041100D    DISPLAY '700-INSERT-DZ01RSTV.'                               04110000
041200     EXEC SQL                                                     04120000
041300          INSERT INTO DZ01RSTV                                    04130000
041400                 VALUES (:DCLDZ01RSTV)                            04140000
041500     END-EXEC                                                     04150000
041600                                                                  04160000
041700     EVALUATE SQLCODE                                             04170000
041800         WHEN 0                                                   04180000
041900              CONTINUE                                            04190000
042000         WHEN OTHER                                               04200000
042100              DISPLAY 'ERROR REC NUMBER : ' WS-NB-INPUT-UPD-I     04210000
042200              PERFORM SQLERROR                                    04220000
042300     END-EVALUATE                                                 04230000
042400     .                                                            04240000
042500                                                                  04250000
042600 1100-UPDATE-VMBFAR.                                              04260000
042700D    DISPLAY '1100-UPDATE-VMBFAR.'                                04270000
042800     MOVE 1100 TO SQL-LOCATION                                    04280000
042900                                                                  04290000
043000     EXEC SQL                                                     04300000
043100       UPDATE DZBFARTV                                            04310000
043200         SET DA_INFSDGD_479BFAR = :DCLDZBFARTV.DA-INFSDGD-479BFAR 04320000
043300           , TS_UPDATE_479BFAR  = :DCLDZBFARTV.TS-UPDATE-479BFAR  04330000
043400           , ID_USERID_479BFAR  = :DCLDZBFARTV.ID-USERID-479BFAR  04340000
043500       WHERE CT_TGDSERV_479BFAR = :DCLDZBFARTV.CT-TGDSERV-479BFAR 04350000
043600         AND NR_CIOFMAS_479BFAR = :DCLDZBFARTV.NR-CIOFMAS-479BFAR 04360000
043700         AND DA_CRFMAS_479BFAR  = :DCLDZBFARTV.DA-CRFMAS-479BFAR  04370000
043800         AND NR_IDFMAS_479BFAR  = :DCLDZBFARTV.NR-IDFMAS-479BFAR  04380000
043900         AND CT_OPDFMAS_479BFAR = :DCLDZBFARTV.CT-OPDFMAS-479BFAR 04390000
044000         AND CT_OPGFMAS_479BFAR = :DCLDZBFARTV.CT-OPGFMAS-479BFAR 04400000
044100       QUERYNO 442                                                04410000
044200     END-EXEC                                                     04420000
044300                                                                  04430000
044400     EVALUATE SQLCODE                                             04440000
044500         WHEN 0                                                   04450000
044600              ADD 1 TO WS-NB-BFAR-UPD-I                           04460000
044700         WHEN OTHER                                               04470000
044800              DISPLAY 'ERROR REC NUMBER : ' WS-NB-INPUT-UPD-I     04480000
044900              PERFORM SQLERROR                                    04490000
045000     END-EVALUATE                                                 04500000
045100     .                                                            04510000
045200                                                                  04520000
045300* SQLERROR ROUTINE.                                               04530000
045400     EXEC SQL                                                     04540000
045500          INCLUDE SQLERROR                                        04550000
045600     END-EXEC.                                                    04560000
045700                                                                  04570000
