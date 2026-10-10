000010 CBL ARITH(EXTEND)                                                00010000
000020 IDENTIFICATION DIVISION.                                         00020000
000030*========================                                         00030000
000040 PROGRAM-ID.   VMDZ4420.                                          00040000
000050 AUTHOR.       ANUJA DHURI.                                       00050000
000060 DATE-WRITTEN. APRIL 2026.                                        00060000
000070                                                                  00070000
000080******************************************************************00080000
000090*                                                                *00090000
000100*                INFORMATIONAL KASBON 2.                         *00100000
000110*                                                                *00110000
000120******************************************************************00120000
000130*                                                                *00130000
000140*            COMPARISON DATABASE AND INVENTORY                   *00140000
000150*            -----------------------------------                 *00150000
000160*                                                                *00160000
000170*            SECOND PROGRAM :                                    *00170000
000180*                                                                *00180000
000190*            SEARCHING ALL EFFECTS AND ALL EVENTS                *00190000
000200*            WHO ARE STILL ALIVE.                                *00200000
000201*                                                                *00210000
000210******************************************************************00220000
000220* THIS PROGRAM IS BEING USED TO EXTRACT THE INPUT KASBONS DATA   *00230000
000230* FROM FOLLOWING (2) KASBONS DB2 TABLES AND CHECK THE VALID      *00240000
000240* RECORDS AND WRITE THOSE RECORDS INTO OUTPUT FILE.              *00250000
000250*                                                                *00260000
000260* DZBEFFTB(PARENT) ----> DZEVEFTB(CHILD)                         *00270000
000270*                                                                *00280000
000280* DZBEFFTB - SELECT                                              *00290000
000290* DZEVEFTB - SELECT                                              *00300000
000300*                                                                *00310000
000380******************************************************************00320000
000390/                                                                 00330000
000400 ENVIRONMENT DIVISION.                                            00340000
000410*---------------------                                            00350000
000420 INPUT-OUTPUT SECTION.                                            00360000
000430 FILE-CONTROL.                                                    00370000
000440     SELECT UITBST ASSIGN TO UT-S-DD005.                          00380000
000480/                                                                 00390000
000490 DATA DIVISION.                                                   00400000
000500*--------------                                                   00410000
000510 FILE SECTION.                                                    00420000
000520*                                                                 00430000
000530 FD  UITBST                                                       00440000
000540     BLOCK CONTAINS 0 RECORDS                                     00450000
000550     RECORD CONTAINS 50 CHARACTERS                                00460000
000560     RECORDING MODE F                                             00470000
000570     LABEL RECORDS STANDARD.                                      00480000
000571                                                                  00490000
000580 01  UITRECORD.                                                   00500000
000610     03  UIT-AM-CN-STOCK          PIC S9(13)V99 COMP-3.           00510000
000620     03  UIT-AM-CND-STOCK         PIC S9(13)V99 COMP-3.           00520000
000630     03  UIT-NR-CIO-CRE           PIC 9(6).                       00530000
000640     03  UIT-NR-ID                PIC X(04).                      00540000
000641     03  UIT-NS-SEQ               PIC 9(04).                      00550000
000642     03  UIT-DA-UBSEC             PIC X(08).                      00560000
000643     03  UIT-NR-ST                PIC X(12).                      00570000
000650*                                                                 00580000
000690 WORKING-STORAGE SECTION.                                         00590000
000700*                                                                 00600000
000710 01  WS-TE-WORK.                                                  00610000
000720     10  WS-STATUS                PIC X       VALUE SPACE.        00620000
000721     10  SW-STATUS-D              PIC X       VALUE 'N'.          00630000
000730     10  USERABEN                 PIC X(8)    VALUE 'USERABEN'.   00640000
000740     10  WS-NB-BEFF-COUNT         PIC 9(7)    COMP-3 VALUE ZEROES.00650000
000750     10  WS-NB-OUTPUT-COUNT       PIC 9(7)    COMP-3 VALUE ZEROES.00660000
000751     10  CS-PROGRAM               PIC X(8)    VALUE 'VMDZ4420'.   00670000
000752     10  WS-NR-ID-GOOD.                                           00680000
000753         20  WS-NR-CIO-CRE        PIC 9(8)    VALUE ZEROES.       00690000
000760         20  WS-DA-CR-CRE         PIC 9(8)    VALUE ZEROES.       00700000
000770         20  WS-NR-ID-CRE         PIC 9(6)    VALUE ZEROES.       00710000
000780         20  WS-CT-OPD-CRE        PIC 9(3)    VALUE ZEROES.       00720000
000790         20  WS-CT-OPG-CRE        PIC 9(3)    VALUE ZEROES.       00730000
000810*                                                                 00740000
000820 01  WS-DZBFFSC1-FLAG             PIC X.                          00750000
000830     88  DZBEFFC1-NOT-EOC         VALUE 'N'.                      00760000
000840     88  DZBEFFC1-EOC             VALUE 'Y'.                      00770000
000850                                                                  00780000
000860 01  WS-DZEVEFC1-FLAG             PIC X.                          00790000
000870     88  DZEVEFC1-NOT-EOC         VALUE 'N'.                      00800000
000880     88  DZEVEFC1-EOC             VALUE 'Y'.                      00810000
000890                                                                  00820000
000900 01  WS-TIMESTAMP-FIELDS.                                         00830000
001000     05 TS-SYSTEM.                                                00840000
001100        10  DA-SYS.                                               00850000
001200            15  DA-SYS-CCYY.                                      00860000
001300                20  CC            PIC X(2).                       00870000
001400                20  YY            PIC X(2).                       00880000
001500            15  MM                PIC X(2).                       00890000
001600            15  DD                PIC X(2).                       00900000
001700        10  HR-SYS.                                               00910000
001800            15  HH                PIC X(2).                       00920000
001900            15  MI                PIC X(2).                       00930000
002000            15  SS                PIC X(2).                       00940000
002100            15  TT                PIC X(2).                       00950000
002200     05 TS-TIMESTAMP.                                             00960000
002300        10  CC                    PIC X(2).                       00970000
002400        10  YY                    PIC X(2).                       00980000
002500        10  TE-MARKER1            PIC X             VALUE '-'.    00990000
002600        10  MM                    PIC X(2).                       01000000
002700        10  TE-MARKER2            PIC X             VALUE '-'.    01010000
002800        10  DD                    PIC X(2).                       01020000
002900        10  TE-MARKER3            PIC X             VALUE '-'.    01030000
003000        10  HH                    PIC X(2).                       01040000
003100        10  TE-MARKER4            PIC X             VALUE '.'.    01050000
003200        10  MI                    PIC X(2).                       01060000
003300        10  TE-MARKER5            PIC X             VALUE '.'.    01070000
003400        10  SS                    PIC X(2).                       01080000
003500        10  TE-MARKER6            PIC X             VALUE '.'.    01090000
003600        10  TT                    PIC X(2).                       01100000
003700        10  NNNN                  PIC 9(04)         VALUE 0.      01110000
003800                                                                  01120000
003900 01 WS-DATUMVELDEN.                                               01130000
004900    03  DA-CCYYMMDD.                                              01140000
005000        05  CC                    PIC 99       VALUE ZERO.        01150000
005100        05  YY                    PIC 99       VALUE ZERO.        01160000
005200        05  MM                    PIC 99       VALUE ZERO.        01170000
005300        05  DD                    PIC 99       VALUE ZERO.        01180000
005400    03  DA-CCYYMMDD-R REDEFINES DA-CCYYMMDD.                      01190000
005500        05  CCYY                  PIC 9999.                       01200000
005600        05  MM                    PIC 99.                         01210000
005700        05  DD                    PIC 99.                         01220000
005800    03  DA-DD-MM-CCYY.                                            01230000
005900        05  DD                    PIC 9(02).                      01240000
006000        05  TE-MARKER5            PIC X        VALUE '.'.         01250000
006100        05  MM                    PIC 9(02).                      01260000
006200        05  TE-MARKER6            PIC X        VALUE '.'.         01270000
006300        05  CCYY                  PIC 9(04).                      01280000
006400    02  HELP-DA-CREVTPD-479EVEF   PIC 9(8)     VALUE ZEROES.      01290000
006401                                                                  01300000
006402*----- FIELDS ESDATMAS ------------------------------------------*01310000
006403     COPY ESDATMAS.                                               01320000
006404*----- FIELDS PARAMETER DATE ------------------------------------*01330000
006405 01  ZONE-DATONLY.                                                01340000
006406     03  DATE6R-WS.                                               01350000
006407         05  D-YEAR               PIC 99.                         01360000
006408         05  D-MONTH              PIC 99.                         01370000
006409         05  D-DAY                PIC 99.                         01380000
006410     03  DATE6 REDEFINES DATE6R-WS.                               01390000
006411         05  D-DAY                PIC 99.                         01400000
006412         05  D-MONTH              PIC 99.                         01410000
006413         05  D-YEAR               PIC 99.                         01420000
006414     03  DATE8.                                                   01430000
006415         05  D-DAY                PIC 99.                         01440000
006416         05  D-MONTH              PIC 99.                         01450000
006417         05  D-CENT               PIC 99.                         01460000
006418         05  D-YEAR               PIC 99.                         01470000
006419     03  PARMDATE.                                                01480000
006420         05  D-YEAR               PIC 9(4).                       01490000
006421         05  D-MONTH              PIC 9(2).                       01500000
006422         05  D-DAY                PIC 9(2).                       01510000
006423*                                                                 01520000
006424*---- INCLUDE FOR DB2 ------------------------------------------* 01530000
006425     EXEC SQL INCLUDE SQLERRWS END-EXEC.                          01540000
006426     EXEC SQL INCLUDE SQLCA    END-EXEC.                          01550000
006427                                                                  01560000
006428*---- INCLUDE VIEWS --------------------------------------------* 01570000
006429     EXEC SQL INCLUDE DZBEFFTV END-EXEC.                          01580000
006430     EXEC SQL INCLUDE DZEVEFTV END-EXEC.                          01590000
006440                                                                  01600000
006450* DECLARE CURSOR FOR BEFF TABLE                                   01610000
006460* ------------------------------                                  01620000
006470*                                                                 01630000
006480     EXEC SQL DECLARE DZBEFFC1 CURSOR WITH HOLD FOR               01640000
006490       SELECT CO_IDPRKSK_479BEFF                                  01650000
006500            , NS_IRMOSTK_479BEFF                                  01660000
006600            , DA_UBSECIS_479BEFF                                  01670000
006700            , AM_CNSTK_479BEFF                                    01680000
006800            , AM_CNDSTK_479BEFF                                   01690000
006900            , CT_RKTPROD_479BEFF                                  01700000
007000            , NR_IDSTOCK_479BEFF                                  01710000
007100            , NR_CDSTK_479BEFF                                    01720000
007200            , NS_DBSTK_479BEFF                                    01730000
007300       FROM DZBEFFTV                                              01740000
007400       FOR READ ONLY                                              01750000
007410              QUERYNO 176                                         01760000
007500     END-EXEC                                                     01770000
007600*                                                                 01780000
007700* DECLARE CURSOR FOR EVEF TABLE                                   01790000
007800* ------------------------------                                  01800000
007900*                                                                 01810000
008000     EXEC SQL DECLARE DZEVEFC1 CURSOR WITH HOLD FOR               01820000
008100       SELECT CO_STEVPRN_479EVEF                                  01830000
008200            , CT_RKTEVPR_479EVEF                                  01840000
008300            , DA_CREVTPD_479EVEF                                  01850000
008400            , NR_IDGOOD_479EVEF                                   01860000
008500            , NR_ID_479EVEF                                       01870000
008600       FROM DZEVEFTV                                              01880000
008700      WHERE CT_RKTPROD_479BEFF = :DCLDZBEFFTV.CT-RKTPROD-479BEFF  01890000
008800        AND NR_IDSTOCK_479BEFF = :DCLDZBEFFTV.NR-IDSTOCK-479BEFF  01900000
008900        AND NR_CDSTK_479BEFF   = :DCLDZBEFFTV.NR-CDSTK-479BEFF    01910000
009000        AND NS_DBSTK_479BEFF   = :DCLDZBEFFTV.NS-DBSTK-479BEFF    01920000
009100       ORDER BY NR_ID_479EVEF DESC                                01930000
009200       FOR READ ONLY                                              01940000
009210              QUERYNO 195                                         01950000
009300     END-EXEC.                                                    01960000
009301*                                                                 01970000
009302 LINKAGE SECTION.                                                 01980000
009303 01  PARAM-DATONLY.                                               01990000
009304     03  L-PARAM                  PIC S9(4) COMP.                 02000000
009305     03  DATUMLS.                                                 02010000
009306         05  DATE-IND             PIC X.                          02020000
009307         05  DATE8-LS             PIC X(8).                       02030000
009308     EJECT                                                        02040000
009309 PROCEDURE DIVISION USING PARAM-DATONLY.                          02050000
009310*                                                                 02060000
009311* INITIALISATIE                                                   02070000
009312*                                                                 02080000
009313     IF DATE-IND = '0'                                            02090000
009314         ACCEPT DATE6R-WS FROM DATE                               02100000
009315         MOVE CORR DATE6R-WS      TO DATE8                        02110000
009316         IF D-YEAR OF DATE8 > 60                                  02120000
009317              MOVE 19 TO D-CENT OF DATE8                          02130000
009318         ELSE MOVE 20 TO D-CENT OF DATE8                          02140000
009319         END-IF                                                   02150000
009320         MOVE CORR DATE8          TO DATE6                        02160000
009321     ELSE                                                         02170000
009322         MOVE DATE8-LS            TO DATE8                        02180000
009323         MOVE CORR DATE8          TO DATE6                        02190000
009324     END-IF.                                                      02200000
009325     MOVE  DATE6                 TO ES-DATUM.                     02210000
009326     MOVE  ZEROES                TO ES-DAGEN, ES-TYPE-DAG.        02220000
009327     MOVE  '+'                   TO ES-PLUS-MIN.                  02230000
009328*                                                                 02240000
009329     CALL ESDATMAS USING ES-DATUM ES-DAGEN ES-TYPE-DAG ES-PLUS-MIN02250000
009330                         ES-ANTWOORD ES-RETURN-CODE ES-WERKZONE.  02260000
009331*                                                                 02270000
009332     IF ES-RETURN-CODE = '0'                                      02280000
009333          MOVE ES-JJJJ             TO D-YEAR OF PARMDATE          02290000
009334          MOVE ES-MM               TO D-MONTH OF PARMDATE         02300000
009335          MOVE ES-DD               TO D-DAY  OF PARMDATE          02310000
009336     ELSE DISPLAY '***********************************'           02320000
009337          DISPLAY ' '                                             02330000
009338          DISPLAY 'PARAMETER DATE IN ERROR = ' DATE6              02340000
009339          DISPLAY ' '                                             02350000
009340          DISPLAY '***********************************'           02360000
009341          CALL USERABEN                                           02370000
009342     END-IF.                                                      02380000
009343*                                                                 02390000
009344     MOVE CS-PROGRAM   TO PROGRAM-NAME                            02400000
009345     PERFORM 600-GET-TIMESTAMP                                    02410000
009346                                                                  02420000
009347     OPEN OUTPUT UITBST.                                          02430000
009348*                                                                 02440000
009349     INITIALIZE DCLDZBEFFTV                                       02450000
009350**** READ PARENT TABLE BEFF                                       02460000
009360     PERFORM 710-OPEN-DZBEFFC1                                    02470000
009370     PERFORM 720-FETCH-DZBEFFC1 UNTIL DZBEFFC1-EOC                02480000
009380     PERFORM 730-CLOSE-DZBEFFC1                                   02490000
009381                                                                  02500000
009390     CLOSE UITBST                                                 02510000
009400                                                                  02520000
009500     DISPLAY 'TOTAL BEFF RECORDS   : ' WS-NB-BEFF-COUNT           02530000
009600     DISPLAY 'TOTAL OUTPUT RECORDS : ' WS-NB-OUTPUT-COUNT         02540000
009610                                                                  02550000
009700     STOP RUN.                                                    02560000
009701/                                                                 02570000
009702 HOOFDVERWERKING.                                                 02580000
009703*                                                                 02590000
009704* SEARCH FOR ALL EVENTS AT AN EFFECT                              02600000
009705*                                                                 02610000
009706     MOVE SPACE TO WS-STATUS                                      02620000
009707     INITIALIZE DCLDZEVEFTV                                       02630000
009708                                                                  02640000
009709**** READ CHILD TABLE EVEF                                        02650000
009710     PERFORM 810-OPEN-DZEVEFC1                                    02660000
009720                                                                  02670000
009730     MOVE 'N' TO SW-STATUS-D                                      02680000
009740     PERFORM 820-FETCH-DZEVEFC1 UNTIL DZEVEFC1-EOC OR             02690000
009750                                      SW-STATUS-D = 'Y'           02700000
009760     PERFORM 830-CLOSE-DZEVEFC1                                   02710000
009770                                                                  02720000
009780**** CHECK THE CONDITION FOR WRITING THE RECORD INTO OUTPUT FILE  02730000
009790     IF NOT SW-STATUS-D = 'Y'                                     02740000
009800        IF WS-STATUS = 'C'                                        02750000
009900           PERFORM WRITE-UITRECORD                                02760000
010000           ADD 1 TO WS-NB-OUTPUT-COUNT                            02770000
010100        END-IF                                                    02780000
010101     END-IF.                                                      02790000
010102*                                                                 02800000
010103 VERWERK-VMBEVEF.                                                 02810000
010104     MOVE ZEROES            TO DA-CCYYMMDD                        02820000
010105                               HELP-DA-CREVTPD-479EVEF            02830000
010106     MOVE DA-CREVTPD-479EVEF OF DCLDZEVEFTV  TO DA-DD-MM-CCYY     02840000
010107     EVALUATE TRUE                                                02850000
010108      WHEN DA-DD-MM-CCYY = '01.01.0001'                           02860000
010109           MOVE ZEROES                TO DA-CCYYMMDD-R            02870000
010120      WHEN DA-DD-MM-CCYY = '31.12.9999'                           02880000
010130           MOVE '99999999'            TO DA-CCYYMMDD-R            02890000
010140      WHEN OTHER                                                  02900000
010150           MOVE CCYY OF DA-DD-MM-CCYY TO CCYY OF DA-CCYYMMDD-R    02910000
010160           MOVE MM   OF DA-DD-MM-CCYY TO MM   OF DA-CCYYMMDD-R    02920000
010170           MOVE DD   OF DA-DD-MM-CCYY TO DD   OF DA-CCYYMMDD-R    02930000
010180     END-EVALUATE                                                 02940000
010190     MOVE DA-CCYYMMDD-R               TO HELP-DA-CREVTPD-479EVEF  02950000
010191                                                                  02960000
010192     IF HELP-DA-CREVTPD-479EVEF NOT > PARMDATE                    02970000
010193        IF CT-RKTEVPR-479EVEF OF DCLDZEVEFTV = '0060' AND         02980000
010194           WS-STATUS NOT = 'D'                                    02990000
010195           MOVE 'C' TO WS-STATUS                                  03000000
010196           MOVE NR-IDGOOD-479EVEF TO WS-NR-ID-GOOD                03010000
010197        ELSE                                                      03020000
010198           IF CT-RKTEVPR-479EVEF OF DCLDZEVEFTV = '0168' AND      03030000
010199              CO-STEVPRN-479EVEF OF DCLDZEVEFTV NOT = '1'         03040000
010200              MOVE 'D' TO WS-STATUS                               03050000
010201              MOVE 'Y' TO SW-STATUS-D                             03060000
010202           ELSE                                                   03070000
010203              IF CT-RKTEVPR-479EVEF OF DCLDZEVEFTV = '0217' AND   03080000
010204                 WS-STATUS = SPACE                                03090000
010205                 MOVE 'S' TO WS-STATUS                            03100000
010206              END-IF                                              03110000
010207           END-IF                                                 03120000
010208        END-IF                                                    03130000
010209     END-IF.                                                      03140000
010210/                                                                 03150000
010220 WRITE-UITRECORD.                                                 03160000
010230     INITIALIZE UITRECORD                                         03170000
010231                                                                  03180000
010232     MOVE AM-CNSTK-479BEFF OF DCLDZBEFFTV   TO UIT-AM-CN-STOCK    03190000
010233     MOVE AM-CNDSTK-479BEFF OF DCLDZBEFFTV  TO UIT-AM-CND-STOCK   03200000
010234     MOVE WS-NR-CIO-CRE                     TO UIT-NR-CIO-CRE     03210000
010235     MOVE CO-IDPRKSK-479BEFF OF DCLDZBEFFTV TO UIT-NR-ID          03220000
010236     MOVE NS-IRMOSTK-479BEFF OF DCLDZBEFFTV TO UIT-NS-SEQ         03230000
010237     MOVE NR-IDSTOCK-479BEFF OF DCLDZBEFFTV TO UIT-NR-ST          03240000
010238                                                                  03250000
010239     MOVE ZEROES                            TO DA-CCYYMMDD        03260000
010240     MOVE DA-UBSECIS-479BEFF OF DCLDZBEFFTV TO DA-DD-MM-CCYY      03270000
010250     EVALUATE TRUE                                                03280000
010260      WHEN DA-DD-MM-CCYY = '01.01.0001'                           03290000
010270           MOVE ZEROES                TO DA-CCYYMMDD-R            03300000
010280      WHEN DA-DD-MM-CCYY = '31.12.9999'                           03310000
010290           MOVE '99999999'            TO DA-CCYYMMDD-R            03320000
010300      WHEN OTHER                                                  03330000
010400           MOVE CCYY OF DA-DD-MM-CCYY TO CCYY OF DA-CCYYMMDD-R    03340000
010500           MOVE MM   OF DA-DD-MM-CCYY TO MM   OF DA-CCYYMMDD-R    03350000
010600           MOVE DD   OF DA-DD-MM-CCYY TO DD   OF DA-CCYYMMDD-R    03360000
010700     END-EVALUATE                                                 03370000
010701     MOVE DA-CCYYMMDD-R               TO UIT-DA-UBSEC             03380000
010702     WRITE UITRECORD.                                             03390000
010703                                                                  03400000
010704 600-GET-TIMESTAMP.                                               03410000
010705D    DISPLAY '600-GET-TIMESTAMP.'                                 03420000
010706     MOVE FUNCTION CURRENT-DATE            TO TS-SYSTEM.          03430000
010707     MOVE CC OF TS-SYSTEM                  TO CC OF TS-TIMESTAMP  03440000
010708     MOVE YY OF TS-SYSTEM                  TO YY OF TS-TIMESTAMP  03450000
010709     MOVE MM OF TS-SYSTEM                  TO MM OF TS-TIMESTAMP  03460000
010710     MOVE DD OF TS-SYSTEM                  TO DD OF TS-TIMESTAMP  03470000
010720     MOVE HH OF TS-SYSTEM                  TO HH OF TS-TIMESTAMP  03480000
010730     MOVE MI OF TS-SYSTEM                  TO MI OF TS-TIMESTAMP  03490000
010740     MOVE SS OF TS-SYSTEM                  TO SS OF TS-TIMESTAMP  03500000
010750     MOVE TT OF TS-SYSTEM                  TO TT OF TS-TIMESTAMP  03510000
010760     DISPLAY 'TIMESTAMP: ' TS-TIMESTAMP                           03520000
010770     .                                                            03530000
010780*---------------------------------------------------------------* 03540000
010790*    OPEN CURSOR                                                  03550000
010800*---------------------------------------------------------------* 03560000
010900 710-OPEN-DZBEFFC1.                                               03570000
011000D    DISPLAY '71O-OPEN-DZBEFFC1.'                                 03580000
011100     MOVE 710    TO SQL-LOCATION                                  03590000
011200                                                                  03600000
011300     EXEC SQL                                                     03610000
011400       OPEN DZBEFFC1                                              03620000
011500     END-EXEC                                                     03630000
011600                                                                  03640000
011700     EVALUATE SQLCODE                                             03650000
011800       WHEN ZERO                                                  03660000
011900            SET DZBEFFC1-NOT-EOC TO TRUE                          03670000
012000       WHEN OTHER                                                 03680000
012100            DISPLAY 'ERROR WHILE OPENING CURSOR DZBEFFC1'         03690000
012200            PERFORM SQLERROR                                      03700000
012300     END-EVALUATE                                                 03710000
012400     .                                                            03720000
012500*---------------------------------------------------------------* 03730000
012600*    FETCH CURSOR                                                 03740000
012700*---------------------------------------------------------------* 03750000
012800 720-FETCH-DZBEFFC1.                                              03760000
012900D    DISPLAY '720-FETCH-DZBEFFC1.'                                03770000
013000     MOVE 720    TO SQL-LOCATION                                  03780000
013100                                                                  03790000
013200     EXEC SQL                                                     03800000
013300       FETCH DZBEFFC1                                             03810000
013400        INTO :DCLDZBEFFTV.CO-IDPRKSK-479BEFF                      03820000
013500           , :DCLDZBEFFTV.NS-IRMOSTK-479BEFF                      03830000
013600           , :DCLDZBEFFTV.DA-UBSECIS-479BEFF                      03840000
013700           , :DCLDZBEFFTV.AM-CNSTK-479BEFF                        03850000
013800           , :DCLDZBEFFTV.AM-CNDSTK-479BEFF                       03860000
013900           , :DCLDZBEFFTV.CT-RKTPROD-479BEFF                      03870000
014000           , :DCLDZBEFFTV.NR-IDSTOCK-479BEFF                      03880000
014100           , :DCLDZBEFFTV.NR-CDSTK-479BEFF                        03890000
014200           , :DCLDZBEFFTV.NS-DBSTK-479BEFF                        03900000
014300     END-EXEC                                                     03910000
014400                                                                  03920000
014500     EVALUATE SQLCODE                                             03930000
014600       WHEN ZERO                                                  03940000
014700            ADD 1 TO WS-NB-BEFF-COUNT                             03950000
014800            PERFORM HOOFDVERWERKING                               03960000
014900       WHEN 100                                                   03970000
015000            SET DZBEFFC1-EOC TO TRUE                              03980000
015100       WHEN OTHER                                                 03990000
015200            DISPLAY 'ERROR WHILE FETCHING CURSOR DZBEFFC1'        04000000
015300            PERFORM SQLERROR                                      04010000
015400     END-EVALUATE                                                 04020000
015500     .                                                            04030000
015600*---------------------------------------------------------------* 04040000
015700*    CLOSE CURSOR                                                 04050000
015800*---------------------------------------------------------------* 04060000
015900 730-CLOSE-DZBEFFC1.                                              04070000
016000D    DISPLAY '730-CLOSE-DZBEFFC1.'                                04080000
016100     MOVE 730    TO SQL-LOCATION                                  04090000
016200                                                                  04100000
016300     EXEC SQL                                                     04110000
016400       CLOSE DZBEFFC1                                             04120000
016500     END-EXEC                                                     04130000
016600                                                                  04140000
016700     EVALUATE SQLCODE                                             04150000
016800       WHEN ZERO                                                  04160000
016900            CONTINUE                                              04170000
017000       WHEN OTHER                                                 04180000
017100            DISPLAY 'ERROR WHILE CLOSING CURSOR DZBEFFC1'         04190000
017200            PERFORM SQLERROR                                      04200000
017300     END-EVALUATE                                                 04210000
017400     .                                                            04220000
017500*---------------------------------------------------------------* 04230000
017600*    OPEN CURSOR                                                  04240000
017700*---------------------------------------------------------------* 04250000
017800 810-OPEN-DZEVEFC1.                                               04260000
017900D    DISPLAY '81O-OPEN-DZEVEFC1.'                                 04270000
018000     MOVE 810    TO SQL-LOCATION                                  04280000
018100                                                                  04290000
018200     EXEC SQL                                                     04300000
018300       OPEN DZEVEFC1                                              04310000
018400     END-EXEC                                                     04320000
018500                                                                  04330000
018600     EVALUATE SQLCODE                                             04340000
018700       WHEN ZERO                                                  04350000
018800            SET DZEVEFC1-NOT-EOC TO TRUE                          04360000
018900       WHEN OTHER                                                 04370000
019000            DISPLAY 'ERROR WHILE OPENING CURSOR DZEVEFC1'         04380000
019100            PERFORM SQLERROR                                      04390000
019200     END-EVALUATE                                                 04400000
019300     .                                                            04410000
019400*---------------------------------------------------------------* 04420000
019500*    FETCH CURSOR                                                 04430000
019600*---------------------------------------------------------------* 04440000
019700 820-FETCH-DZEVEFC1.                                              04450000
019800D    DISPLAY '820-FETCH-DZEVEFC1.'                                04460000
019900     MOVE 820    TO SQL-LOCATION                                  04470000
020000                                                                  04480000
020100     EXEC SQL                                                     04490000
020200       FETCH DZEVEFC1                                             04500000
020300        INTO :DCLDZEVEFTV.CO-STEVPRN-479EVEF                      04510000
020400           , :DCLDZEVEFTV.CT-RKTEVPR-479EVEF                      04520000
020500           , :DCLDZEVEFTV.DA-CREVTPD-479EVEF                      04530000
020600           , :DCLDZEVEFTV.NR-IDGOOD-479EVEF                       04540000
020700           , :DCLDZEVEFTV.NR-ID-479EVEF                           04550000
020800     END-EXEC                                                     04560000
020900                                                                  04570000
021000     EVALUATE SQLCODE                                             04580000
021100       WHEN ZERO                                                  04590000
021200            PERFORM VERWERK-VMBEVEF                               04600000
021300       WHEN 100                                                   04610000
021400            SET DZEVEFC1-EOC TO TRUE                              04620000
021500       WHEN OTHER                                                 04630000
021600            DISPLAY 'ERROR WHILE FETCHING CURSOR DZEVEFC1'        04640000
021700            DISPLAY 'CT-RKT-PROD = ' CT-RKTPROD-479BEFF           04650000
021800                                     OF DCLDZBEFFTV               04660000
021900            DISPLAY 'NR-ID-STOCK = ' NR-IDSTOCK-479BEFF           04670000
022000                                     OF DCLDZBEFFTV               04680000
022100            DISPLAY 'NR-CD-STOCK = ' NR-CDSTK-479BEFF             04690000
022200                                     OF DCLDZBEFFTV               04700000
022300            DISPLAY 'NR-DB-STOCK = ' NS-DBSTK-479BEFF             04710000
022400                                     OF DCLDZBEFFTV               04720000
022500            PERFORM SQLERROR                                      04730000
022600     END-EVALUATE                                                 04740000
022700     .                                                            04750000
022800*---------------------------------------------------------------* 04760000
022900*    CLOSE CURSOR                                                 04770000
023000*---------------------------------------------------------------* 04780000
023100 830-CLOSE-DZEVEFC1.                                              04790000
023200D    DISPLAY '830-CLOSE-DZEVEFC1.'                                04800000
023300     MOVE 830    TO SQL-LOCATION                                  04810000
023400                                                                  04820000
023500     EXEC SQL                                                     04830000
023600       CLOSE DZEVEFC1                                             04840000
023700     END-EXEC                                                     04850000
023800                                                                  04860000
023900     EVALUATE SQLCODE                                             04870000
024000       WHEN ZERO                                                  04880000
024100            CONTINUE                                              04890000
024200       WHEN OTHER                                                 04900000
024300            DISPLAY 'ERROR WHILE CLOSING CURSOR DZEVEFC1'         04910000
024400            PERFORM SQLERROR                                      04920000
024500     END-EVALUATE                                                 04930000
024600     .                                                            04940000
024700                                                                  04950000
024800* SQLERROR ROUTINE.                                               04960000
024900     EXEC SQL                                                     04970000
025000          INCLUDE SQLERROR                                        04980000
025100     END-EXEC.                                                    04990000
