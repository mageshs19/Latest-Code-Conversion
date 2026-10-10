000010 CBL NOSQL                                                        00000010
000100 IDENTIFICATION DIVISION.                                         00000100
000200*------------------------                                         00000200
000300 PROGRAM-ID.    VM1BD526.                                         00000300
000400 AUTHOR.        ERIK DE RIJCKE (RAET).                            00000400
000500 DATE-WRITTEN.  14-10-86.                                         00000500
000600 DATE-COMPILED.                                                   00000600
000700                                                                  00000700
000800*************************************************************     00000800
000900*                                                           *     00000900
001000*  VERSIE IKB2BIS MET NIEUWE TYPES                          *     00001000
001100*  NEERLEGING - VERNIETIGINGEN EFFECT                       *     00001100
001200*                                                           *     00001200
001300* MODIFIED BY J. CLEMENT : INPUT 400 ---> 600               *     00001300
001400*                          VMBD205A  ---> VMBD205S          *     00001400
001500*                                                           *     00001500
001600* MODIFIED BY P. VERBEEK : AANPASSINGEN JAAR 2000           *     00001600
001700*                                                           *     00001700
001800* MODIFIED BY S. POMPONIO: AANPASSINGEN EURO2000            *     00001800
001900*                          INPUT 600 ---> 800               *     00001900
002000*                          VMBD205S  ---> VMBD205X          *     00002000
002100* MODIFIED BY JEROEN "JEROD" DE SCHUTTER (DOLMEN) - 09/2003 *     00002100
002200*  . AANPASSINGEN IKV. INTEGRATIEPROJECT 6212 :             *     00002200
002300*    DAISY SECURITIES KASBONS                               *     00002300
002400*                                                           *     00002400
002500*************************************************************     00002500
002600                                                                  00002600
002700 ENVIRONMENT DIVISION.                                            00002700
002800*---------------------                                            00002800
002900 CONFIGURATION SECTION.                                           00002900
003000 SOURCE-COMPUTER. IBM-370.                                        00003000
003100 OBJECT-COMPUTER. IBM-370.                                        00003100
003200                                                                  00003200
003300 INPUT-OUTPUT SECTION.                                            00003300
003400 FILE-CONTROL.                                                    00003400
003500     SELECT INFIL ASSIGN TO UT-S-DD020.                           00003500
003600                                                                  00003600
003700 IDMS-CONTROL SECTION.                                            00003700
003800 PROTOCOL. MODE IS BATCH-AUTOSTATUS DEBUG                         00003800
003900           IDMS-RECORDS WITHIN WORKING-STORAGE SECTION.           00003900
004000                                                                  00004000
004100 DATA DIVISION.                                                   00004100
004200*--------------                                                   00004200
004300 FILE SECTION.                                                    00004300
004400 FD  INFIL                                                        00004400
004500     BLOCK CONTAINS 0 RECORDS                                     00004500
004600     LABEL RECORD IS STANDARD                                     00004600
004700     RECORDING MODE F                                             00004700
004800     DATA RECORD IS VMBD205I.                                     00004800
004900                                                                  00004900
005000     COPY VMBD205I.                                               00005000
005100                                                                  00005100
005200 SCHEMA SECTION.                                                  00005200
005300 DB  VMBTS07 WITHIN VMBTSCH.                                      00005300
005400                                                                  00005400
005500 WORKING-STORAGE SECTION.                                         00005500
005600                                                                  00005600
005700 01  WS-HULPVELDEN.                                               00005700
005800     05  SW-EOF              VALUE +0          PIC S9    COMP.    00005800
005900         88 EOF              VALUE +1.                            00005900
006000     05  SW-FFRECAB          VALUE +0          PIC S9    COMP.    00006000
006100         88 FFRECAB-AANW     VALUE +0.                            00006100
006200     05  TELLER                                PIC S9(5) COMP-3.  00006200
006300     05  USERABEN            VALUE 'USERABEN'  PIC X(8).          00006300
006400                                                                  00006400
006500 01  HULP-NR-ID-GOOD.                                             00006500
006600     03  HULP-NR-CIO     PIC 9(8)    COMP-3.                      00006600
006700     03  HULP-DA-CREA    PIC 9(8)    COMP-3.                      00006700
006800     03  HULP-NR-ID      PIC 9(6)    COMP-3.                      00006800
006900     03  HULP-CT-OPD     PIC 999     COMP-3.                      00006900
007000     03  HULP-CT-OPG     PIC 999     COMP-3.                      00007000
007100     03  FILLER          PIC XX      VALUE SPACES.                00007100
007200 01  STOP-DATONLY.                                                00007200
007300     02  DATE-YMD.                                                00007300
007400         03  D-YEAR      PIC 99.                                  00007400
007500         03  D-MONTH     PIC 99.                                  00007500
007600         03  D-DAY       PIC 99.                                  00007600
007700     02  DATE-DMY.                                                00007700
007800         03  D-DAY       PIC 99.                                  00007800
007900         03  D-MONTH     PIC 99.                                  00007900
008000         03  D-YEAR      PIC 99.                                  00008000
008100     02  DATE-YMD8.                                               00008100
008200         03  D-CENT      PIC 99.                                  00008200
008300         03  D-YEAR      PIC 99.                                  00008300
008400         03  D-MONTH     PIC 99.                                  00008400
008500         03  D-DAY       PIC 99.                                  00008500
008600     02  DATE-DMY8.                                               00008600
008700         03  D-DAY       PIC 99.                                  00008700
008800         03  D-MONTH     PIC 99.                                  00008800
008900         03  D-CENT      PIC 99.                                  00008900
009000         03  D-YEAR      PIC 99.                                  00009000
009100                                                                  00009100
009200 LINKAGE SECTION.                                                 00009200
009300 01  PARAM-DATONLY.                                               00009300
009400     03 L-PARAM          PIC S9(4)  COMP.                         00009400
009500     03 DATUMLS.                                                  00009500
009600        05 DAT-IND       PIC X.                                   00009600
009700        05 DATE8-LS      PIC X(8).                                00009700
009800                                                                  00009800
009900 PROCEDURE DIVISION USING PARAM-DATONLY.                          00009900
010000*---------------------------------------                          00010000
010100                                                                  00010100
010200 000-STUUR.                                                       00010200
010300     PERFORM 100-INITIALISATIE.                                   00010300
010400     PERFORM 200-VERWERK-INFIL UNTIL EOF.                         00010400
010500     PERFORM 800-TEST-FFRECAB.                                    00010500
010600     FINISH.                                                      00010600
010700     CLOSE INFIL.                                                 00010700
010800     STOP RUN.                                                    00010800
010900                                                                  00010900
011000 100-INITIALISATIE.                                               00011000
011100     MOVE DATE8-LS       TO DATE-DMY8.                            00011100
011200     MOVE CORR DATE-DMY8 TO DATE-DMY.                             00011200
011300     MOVE CORR DATE-DMY8 TO DATE-YMD.                             00011300
011400     MOVE CORR DATE-DMY8 TO DATE-YMD8.                            00011400
011500                                                                  00011500
011600     COPY IDMS SUBSCHEMA-BINDS.                                   00011600
011700     READY USAGE-MODE IS UPDATE.                                  00011700
011800     OPEN INPUT INFIL.                                            00011800
011900     MOVE 'VM1BDF526-A' TO NM-ID-FF OF FFRECAB.                   00011900
012000     MOVE DATE-YMD8     TO DA-CR-FF OF FFRECAB.                   00012000
012100     MOVE 0 TO NS-SET-FF.                                         00012100
012200     OBTAIN CALC FFRECAB                                          00012200
012300            ON DB-REC-NOT-FOUND                                   00012300
012400               MOVE +1 TO SW-FFRECAB.                             00012400
012500     IF FFRECAB-AANW                                              00012500
012600        MOVE +0  TO TELLER                                        00012600
012700        PERFORM 110-POSITIONEREN-INFIL                            00012700
012800                UNTIL TELLER NOT < NS-REC-FF-IN                   00012800
012900     ELSE                                                         00012900
013000        MOVE '1' TO CT-SET-FF OF FFRECAB                          00013000
013100        MOVE 'A' TO CT-REC-FF OF FFRECAB                          00013100
013200        MOVE SPACES TO GR-REC-FF                                  00013200
013300        MOVE 0   TO NR-KY-FF                                      00013300
013400        MOVE 0   TO NS-REC-FF-A                                   00013400
013500        MOVE 0   TO NS-REC-FF-IN                                  00013500
013600        MOVE 15  TO NB-DAY-FF OF FFRECAB                          00013600
013700     END-IF.                                                      00013700
013800     MOVE +0 TO TELLER.                                           00013800
013900     PERFORM 900-LEES-INFIL.                                      00013900
014000                                                                  00014000
014100 110-POSITIONEREN-INFIL.                                          00014100
014200     ADD +1 TO TELLER.                                            00014200
014300     PERFORM 900-LEES-INFIL.                                      00014300
014400     IF EOF                                                       00014400
014500          PERFORM STOP01.                                         00014500
014600                                                                  00014600
014700 200-VERWERK-INFIL.                                               00014700
014800     ADD +1 TO TELLER.                                            00014800
014900     IF CO-STCIRC-OORD = '1'                                      00014900
015000     THEN PERFORM 210-STORE-EFF                                   00015000
015100     ELSE PERFORM 220-MOD-EVEF                                    00015100
015200     END-IF.                                                      00015200
015300     IF TELLER NOT < +100                                         00015300
015400          PERFORM 800-TEST-FFRECAB                                00015400
015500          COMMIT                                                  00015500
015600          MOVE +0 TO TELLER.                                      00015600
015700     PERFORM 900-LEES-INFIL.                                      00015700
015800                                                                  00015800
015900 210-STORE-EFF.                                                   00015900
016000     MOVE SPACES TO VMBEFF                                        00016000
016100                    VMBEVEF.                                      00016100
016200     MOVE '1002' TO CT-RK-TPROD OF VMBEFF                         00016200
016300     MOVE NR-ST-FORM-AS OF VMBD205I TO NR-ID-STOCK-CD OF VMBEFF.  00016300
016400     MOVE NS-DB-STOCK-FORM-AS       TO NS-DB-STOCK OF VMBEFF.     00016400
016500     MOVE NR-ID-040SECU             TO CO-IDPRKB-STOCK OF VMBEFF. 00016500
016600     MOVE NS-SEQ-040IRMO            TO NS-IRMO-STOCK   OF VMBEFF. 00016600
016700     MOVE DA-UB-FORM-AS OF VMBD205I TO DA-UBSECIS-STOCK OF VMBEFF.00016700
016800     MOVE 0                         TO NR-ID-ISSUE OF VMBEFF      00016800
016900                                       NR-CD-ISSUE OF VMBEFF.     00016900
017000     MOVE DATE-YMD8               TO DA-CR-EVENT-PROD OF VMBEVEF. 00017000
017100     MOVE '0168'                    TO CT-RK-TEVPR OF VMBEVEF.    00017100
017200     MOVE '0219'                    TO CT-RK-TGDSV OF VMBEVEF.    00017200
017300     MOVE NR-CIO-FORM-AS-R          TO HULP-NR-CIO.               00017300
017400     MOVE DA-CREA-FORM-AS-R         TO HULP-DA-CREA.              00017400
017500     MOVE NR-ID-FORM-AS OF VMBD205I TO HULP-NR-ID.                00017500
017600     MOVE CT-OPD-FORM-AS-R          TO HULP-CT-OPD.               00017600
017700     MOVE CT-OPG-FORM-AS-R          TO HULP-CT-OPG.               00017700
017800     MOVE HULP-NR-ID-GOOD           TO NR-ID-GOOD.                00017800
017900     MOVE NR-CIO-FORM-AS OF VMBD205I TO DB-NR-CI.                 00017900
018000                                                                  00018000
018100*                                                                 00018100
018200* STOCKEREN VAN DE RECORDS :                                      00018200
018300*    - VMBWCEF                                                    00018300
018400     MOVE NR-CIO-FORM-AS OF VMBD205I TO NR-CI OF VMBEVEF.         00018400
018500     STORE VMBTL07-R01 WHERE ST-VMBEVEF.                          00018500
018600*=                                                                00018600
018700*=      OBTAIN VMBEFF                                             00018700
018800*=          WHERE CALCKEY EQ KY-EFFECT OF VMBEFF OF LR            00018800
018900*=          ON 0326 RETURN VMBEFF-NOT-FND                         00018900
019000*=      STORE VMBEVEF                                             00019000
019100*=                                                                00019100
019200     IF LR-STATUS = 'VMBEFF-NOT-FND' OR                           00019200
019300                    'LR-ERROR'                                    00019300
019400          PERFORM IDMS-STOP.                                      00019400
019500                                                                  00019500
019600 220-MOD-EVEF.                                                    00019600
019700     MOVE SPACES TO VMBEFF.                                       00019700
019800     MOVE '1002'                 TO CT-RK-TPROD OF VMBEFF.        00019800
019900     MOVE NR-ST-FORM-AS   OF VMBD205I  TO NR-ID-STOCK-CD.         00019900
020000     MOVE NS-DB-STOCK-FORM-AS          TO NS-DB-STOCK.            00020000
020100*                                                                 00020100
020200     OBTAIN FIRST VMBTL07-R01 WHERE ALL-VMBEVEF-BY-VMBEFF AND     00020200
020300            CT-RK-TEVPR = '0168' AND                              00020300
020400            CT-RK-TGDSV = '0219'.                                 00020400
020500     IF LR-STATUS NOT = 'LR-FOUND'                                00020500
020600        DISPLAY ' ** VM1BD526 RECH EVTS SOUSCRIPTION **'          00020600
020700        DISPLAY 'NR-ST:' NR-ST-FORM-AS OF VMBD205I                00020700
020800               ' NS-DB:' NS-DB-STOCK-FORM-AS OF VMBD205I          00020800
020900               ' LR-STATUS:' LR-STATUS                            00020900
021000        CALL USERABEN                                             00021000
021100     END-IF.                                                      00021100
021200                                                                  00021200
021300     MOVE NR-CIO-FORM-AS-R             TO HULP-NR-CIO.            00021300
021400     MOVE DA-CREA-FORM-AS-R            TO HULP-DA-CREA.           00021400
021500     MOVE NR-ID-FORM-AS OF VMBD205I    TO HULP-NR-ID.             00021500
021600     MOVE CT-OPD-FORM-AS-R             TO HULP-CT-OPD.            00021600
021700     MOVE CT-OPG-FORM-AS-R             TO HULP-CT-OPG.            00021700
021800     MOVE HULP-NR-ID-GOOD              TO NR-ID-GOOD.             00021800
021900                                                                  00021900
022000     MODIFY VMBTL07-R01 WHERE MO-VMBEVEF.                         00022000
022100     IF LR-STATUS NOT = 'LR-FOUND'                                00022100
022200        DISPLAY ' ** VM1BD526 UPDATE CLÉ FORM **'                 00022200
022300        DISPLAY 'NR-ST:' NR-ST-FORM-AS OF VMBD205I                00022300
022400               ' NS-DB:' NS-DB-STOCK-FORM-AS OF VMBD205I          00022400
022500               ' LR-STATUS:' LR-STATUS                            00022500
022600        CALL USERABEN                                             00022600
022700     END-IF.                                                      00022700
022800                                                                  00022800
022900 800-TEST-FFRECAB.                                                00022900
023000     IF FFRECAB-AANW                                              00023000
023100          OBTAIN CALC FFRECAB                                     00023100
023200          ADD TELLER TO NS-REC-FF-IN                              00023200
023300          MODIFY FFRECAB                                          00023300
023400     ELSE ADD TELLER TO NS-REC-FF-IN                              00023400
023500          STORE FFRECAB                                           00023500
023600          MOVE +0 TO SW-FFRECAB.                                  00023600
023700                                                                  00023700
023800 900-LEES-INFIL.                                                  00023800
023900     READ INFIL                                                   00023900
024000          AT END MOVE +1 TO SW-EOF.                               00024000
024100                                                                  00024100
024200 STOP01.                                                          00024200
024300     DISPLAY '##&&VM1BD526 - STOP01 : TE WEINIG REC OP INFIL'.    00024300
024400     CALL USERABEN.                                               00024400
024500                                                                  00024500
024600 IDMS-STOP.                                                       00024600
024700     DISPLAY '##&&LR-STATUS    : ', LR-STATUS.                    00024700
024800     DISPLAY '##&&ERROR-STATUS : ', ERROR-STATUS.                 00024800
024900     DISPLAY '##&&DML-SEQUENCE : ', DML-SEQUENCE.                 00024900
025000     ROLLBACK.                                                    00025000
025100     CALL USERABEN.                                               00025100
025200                                                                  00025200
025300 COPY IDMS IDMS-STATUS.                                           00025300
025400                                                                  00025400
025500 IDMS-ABORT.                                                      00025500
