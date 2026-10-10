000100 CBL NOCMPR2,NOFLAGMIG, OPTIMIZE                                  00000100
000200 IDENTIFICATION DIVISION.                                         00000200
000300*------------------------                                         00000300
000400 PROGRAM-ID.     VM4BD302.                                        00000400
000500 AUTHOR.         KRISTINE WULTEPUTTE                              00000500
000600*-----------------------------------------------------------------00000600
000700*         OPHALEN VAN EFFEKTEN MET EVENEMENTEN DIE TERUGBETAALD ZI00000700
000800*         1 MAAND VOOR DE EINDVERVALDAG                           00000800
000900*-----------------------------------------------------------------00000900
001000* 12 NOV 1997 MODIFIED BY PETER VERBEEK                           00001000
001100*             VERWIJDEREN BAREMA DER WAARDEN                      00001100
001200*-----------------------------------------------------------------00001200
001300* 19 JAN 1998 MODIFIED BY PETER VERBEEK                           00001300
001400*             EURO AANPASSINGEN                                   00001400
001500*-----------------------------------------------------------------00001500
001600* 11 DEC 2004 MODIFIED BY NICOLAS JORIS                           00001600
001700*             ADAPTATIONS DAISY SECURITIES SUITE AUX MODIFICATIONS00001700
001800*             DE LA DB.                                           00001800
001900*             CE PROGRAMME EST UNE ADAPTATION DE VM4OM003         00001900
002000*-----------------------------------------------------------------00002000
002100* MODIFIED BY VHEML                                               00002100
002200*   2007/11 : HERCOMPILATIE P20 2767 ENGELS UITTREKSEL            00002200
002300*-----------------------------------------------------------------00002300
002400*                                                                 00002400
002500 DATE-WRITTEN.   JANUARI 93                                       00002500
002600/                                                                 00002600
002700*-----------------------------------------------------------------00002700
002800 ENVIRONMENT DIVISION.                                            00002800
002900*-----------------------------------------------------------------00002900
003000 INPUT-OUTPUT SECTION.                                            00003000
003100 FILE-CONTROL.                                                    00003100
003200     SELECT EMISSIONS-I ASSIGN TO UT-S-DD010.                     00003200
003300     SELECT EFFEKT-O    ASSIGN TO UT-S-DD005.                     00003300
003400*                                                                 00003400
003500 IDMS-CONTROL SECTION.                                            00003500
003600 PROTOCOL. MODE IS BATCH DEBUG                                    00003600
003700           IDMS-RECORDS MANUAL.                                   00003700
003800/                                                                 00003800
003900*-----------------------------------------------------------------00003900
004000 DATA DIVISION.                                                   00004000
004100*-----------------------------------------------------------------00004100
004200 FILE SECTION.                                                    00004200
004300 FD  EMISSIONS-I                                                  00004300
004400     BLOCK CONTAINS 0 RECORDS                                     00004400
004500     RECORD CONTAINS 40 CHARACTERS                                00004500
004600     RECORDING MODE F                                             00004600
004700     LABEL RECORDS STANDARD.                                      00004700
004800 01  EMISSIONS-I-REC PIC X(40).                                   00004800
004900*                                                                 00004900
005000 FD  EFFEKT-O                                                     00005000
005100     BLOCK CONTAINS 0 RECORDS                                     00005100
005200     RECORD CONTAINS 90 CHARACTERS                                00005200
005300     RECORDING MODE F                                             00005300
005400     LABEL RECORDS STANDARD.                                      00005400
005500 01  REFFEKT-O   PIC X(90).                                       00005500
005600*                                                                 00005600
005700 SCHEMA SECTION.                                                  00005700
005800 DB  VMBTS07 WITHIN VMBTSCH.                                      00005800
005900*                                                                 00005900
006000*-----------------------------------------------------------------00006000
006100 WORKING-STORAGE SECTION.                                         00006100
006200*-----------------------------------------------------------------00006200
006300 COPY IDMS SUBSCHEMA-CTRL.                                        00006300
006400 COPY IDMS SUBSCHEMA-LR-CTRL.                                     00006400
006500 COPY IDMS SUBSCHEMA-SSNAME.                                      00006500
006600 COPY IDMS SUBSCHEMA-AREANAMES.                                   00006600
006700 COPY IDMS SUBSCHEMA-RECNAMES.                                    00006700
006800 COPY IDMS SUBSCHEMA-SETNAMES.                                    00006800
006900 COPY IDMS VMBEFF.                                                00006900
007000 COPY IDMS VMBEVEF.                                               00007000
007100 COPY IDMS VMBWCEF.                                               00007100
007200*                                                                 00007200
007300 01  CS-VM9BC50T         PIC X(8)    VALUE 'VM9BC50T'.            00007300
007400 01  WS-VM9BC50I.                                                 00007400
007500     COPY VM9BC50I     REPLACING ==:VM9BC50T:== BY ==BC50I==.     00007500
007600 01  WS-VM9BC50O.                                                 00007600
007700     COPY VM9BC50O     REPLACING ==:VM9BC50T:== BY ==BC50O==.     00007700
007800 01  WS-VM9BC50T.                                                 00007800
007900     05  TE-INTERFACE           PIC  X(001) OCCURS 32000.         00007900
008000 01  INPUT-RECORD.                                                00008000
008100     02  I-CO-INTERNE PIC X(11).                                  00008100
008200     02  I-DA-UB.                                                 00008200
008300         03  DD           PIC 99.                                 00008300
008400         03  FILLER       PIC X.                                  00008400
008500         03  MM           PIC 99.                                 00008500
008600         03  FILLER       PIC X.                                  00008600
008700         03  CCYY         PIC 9999.                               00008700
008800     02 I-DA-UE.                                                  00008800
008900         03  DD           PIC 99.                                 00008900
009000         03  FILLER       PIC X.                                  00009000
009100         03  MM           PIC 99.                                 00009100
009200         03  FILLER       PIC X.                                  00009200
009300         03  CCYY         PIC 9999.                               00009300
009400     02 FILLER PIC X(9).                                          00009400
009500*                                                                 00009500
009600 01  VARIABLES.                                                   00009600
009700     03  WS-DA-UE-MIN-1MAAND.                                     00009700
009800         05 CCYY          PIC 9(4).                               00009800
009900         05 MM            PIC 99.                                 00009900
010000         05 DD            PIC 99.                                 00010000
010100     03  USERABEN                  PIC X(8)    VALUE 'USERABEN'.  00010100
010200     03  SW-EOF                    PIC 9       VALUE 0.           00010200
010300     03  SW-168                    PIC X       VALUE 'N'.         00010300
010400     03  LAATSTE-DA-CR-EVENT-PROD  PIC 9(8)    VALUE 0.           00010400
010500     03  HULP-NR-ID-GOOD.                                         00010500
010600         05  FILLER                PIC 9(8)    COMP-3.            00010600
010700         05  HULP-DA-UB-TRANSF     PIC 9(8)    COMP-3.            00010700
010800         05  FILLER                PIC 9(6)    COMP-3.            00010800
010900         05  CT-OPD                PIC S9(3)   COMP-3.            00010900
011000         05  FILLER                PIC 9(3)    COMP-3.            00011000
011100         05  FILLER                PIC XX.                        00011100
011200*                                                                 00011200
011300     03  LAATSTE-OPD               PIC S9(3)   COMP-3.            00011300
011400     03  LAATSTE-CI                PIC X(6)    VALUE '000000'.    00011400
011500 01  UITREC.                                                      00011500
011600     03  UIT-NR-CI            PIC  9(06).                         00011600
011700     03  UIT-AM-CN-STOCK      PIC S9(12)V9(6).                    00011700
011800     03  UIT-CO-DEVISE        PIC  X(03).                         00011800
011900     03  FILLER               PIC X(22) VALUE SPACE.              00011900
012000     03  UIT-CO-INTERNE       PIC X(11).                          00012000
012100     03  FILLER               PIC X(12) VALUE SPACE.              00012100
012200     03  UIT-NR-ID-STOCK-CD   PIC  9(13).                         00012200
012300     03  FILLER               PIC  X(05) VALUE SPACES.            00012300
012400*                                                                 00012400
012500 01  ZONE-DATONLY.                                                00012500
012600     02  WS-DA-YMD.                                               00012600
012700         03  YY          PIC 99.                                  00012700
012800         03  MM          PIC 99.                                  00012800
012900         03  DD          PIC 99.                                  00012900
013000*                                                                 00013000
013100     02  WS-DA-DMY.                                               00013100
013200         03  DD          PIC 99.                                  00013200
013300         03  MM          PIC 99.                                  00013300
013400         03  YY          PIC 99.                                  00013400
013500*                                                                 00013500
013600     02  WS-DA-CYMD-N    PIC 9(8).                                00013600
013700     02  WS-DA-CYMD REDEFINES WS-DA-CYMD-N.                       00013700
013800         03  CCYY        PIC 9999.                                00013800
013900         03  MM          PIC 99.                                  00013900
014000         03  DD          PIC 99.                                  00014000
014100*                                                                 00014100
014200     02  WS-DA-UE.                                                00014200
014300         03  CCYY        PIC 9999.                                00014300
014400         03  MM          PIC 99.                                  00014400
014500         03  DD          PIC 99.                                  00014500
014600*                                                                 00014600
014700*-----------------------------------------------------------------00014700
014800 LINKAGE SECTION.                                                 00014800
014900*-----------------------------------------------------------------00014900
015000 01  PARAM-DATONLY.                                               00015000
015100     03  LS-PARAM        PIC S9(4) COMP.                          00015100
015200     03  LS-DATE-IND     PIC X.                                   00015200
015300     03  LS-DA-DMY.                                               00015300
015400         05  DD          PIC 99.                                  00015400
015500         05  MM          PIC 99.                                  00015500
015600         05  YY          PIC 99.                                  00015600
015700/                                                                 00015700
015800*-----------------------------------------------------------------00015800
015900 PROCEDURE DIVISION USING PARAM-DATONLY.                          00015900
016000*-----------------------------------------------------------------00016000
016100*                                                                 00016100
016200* BEGINVERWERKING                                                 00016200
016300*                                                                 00016300
016400     IF LS-DATE-IND = '0'                                         00016400
016500        ACCEPT WS-DA-YMD FROM DATE                                00016500
016600        MOVE CORR WS-DA-YMD TO WS-DA-DMY                          00016600
016700     ELSE                                                         00016700
016800        MOVE LS-DA-DMY TO WS-DA-DMY                               00016800
016900     END-IF                                                       00016900
017000     MOVE CORR WS-DA-DMY TO WS-DA-CYMD.                           00017000
017100     MOVE YY OF WS-DA-DMY TO CCYY OF WS-DA-CYMD.                  00017100
017200*                                                                 00017200
017300     IF CCYY OF WS-DA-CYMD LESS 80                                00017300
017400        ADD 2000 TO CCYY OF WS-DA-CYMD                            00017400
017500     ELSE                                                         00017500
017600        ADD 1900 TO CCYY OF WS-DA-CYMD                            00017600
017700     END-IF                                                       00017700
017800*                                                                 00017800
017900     MOVE 'VM9BD302' TO PROGRAM-NAME.                             00017900
018000     BIND RUN-UNIT.                                               00018000
018100     IF ERROR-STATUS NOT = '0000'                                 00018100
018200        DISPLAY 'BIND RUN-UNIT MISLUKT '                          00018200
018300        DISPLAY 'ERROR-STATUS ' ERROR-STATUS                      00018300
018400        CALL USERABEN                                             00018400
018500     END-IF                                                       00018500
018600     BIND VMBWCEF.                                                00018600
018700     IF ERROR-STATUS NOT = '0000'                                 00018700
018800        DISPLAY 'BIND VMBWCEF MISLUKT '                           00018800
018900        DISPLAY 'ERROR-STATUS ' ERROR-STATUS                      00018900
019000        CALL USERABEN                                             00019000
019100     END-IF                                                       00019100
019200     BIND VMBEFF.                                                 00019200
019300     IF ERROR-STATUS NOT = '0000'                                 00019300
019400        DISPLAY 'BIND VMBEFF  MISLUKT '                           00019400
019500        DISPLAY 'ERROR-STATUS ' ERROR-STATUS                      00019500
019600        CALL USERABEN                                             00019600
019700     END-IF                                                       00019700
019800     BIND VMBEVEF.                                                00019800
019900     IF ERROR-STATUS NOT = '0000'                                 00019900
020000        DISPLAY 'BIND VMBEVEF MISLUKT '                           00020000
020100        DISPLAY 'ERROR-STATUS ' ERROR-STATUS                      00020100
020200        CALL USERABEN                                             00020200
020300     END-IF                                                       00020300
020400     READY AR-VMBEFF1 USAGE-MODE IS RETRIEVAL.                    00020400
020500     IF ERROR-STATUS NOT = '0000'                                 00020500
020600        DISPLAY 'READY AREA VMBEFF1 MISLUKT '                     00020600
020700        DISPLAY 'ERROR-STATUS ' ERROR-STATUS                      00020700
020800        CALL USERABEN                                             00020800
020900     END-IF                                                       00020900
021000     READY AR-VMBWCEF USAGE-MODE IS RETRIEVAL.                    00021000
021100     IF ERROR-STATUS NOT = '0000'                                 00021100
021200        DISPLAY 'READY AREA VMBWCEF MISLUKT '                     00021200
021300        DISPLAY 'ERROR-STATUS ' ERROR-STATUS                      00021300
021400        CALL USERABEN                                             00021400
021500     END-IF                                                       00021500
021600*                                                                 00021600
021700     OPEN INPUT  EMISSIONS-I                                      00021700
021800          OUTPUT EFFEKT-O.                                        00021800
021900*                                                                 00021900
022000     READ EMISSIONS-I INTO INPUT-RECORD                           00022000
022100        AT END MOVE 1 TO SW-EOF                                   00022100
022200     END-READ.                                                    00022200
022300*                                                                 00022300
022400     PERFORM VERWERK-EMISSIONS UNTIL SW-EOF = 1.                  00022400
022500*                                                                 00022500
022600     CLOSE EMISSIONS-I                                            00022600
022700           EFFEKT-O.                                              00022700
022800*                                                                 00022800
022900     FINISH                                                       00022900
023000     STOP RUN.                                                    00023000
023100/                                                                 00023100
023200*-----------------------------------------------------------------00023200
023300 VERWERK-EMISSIONS.                                               00023300
023400*-----------------------------------------------------------------00023400
023500     MOVE CORR I-DA-UE TO WS-DA-UE                                00023500
023600*                                                                 00023600
023700     MOVE SPACES       TO VMBWCEF                                 00023700
023800     PERFORM CALL-VM9BC50T                                        00023800
023900     MOVE BC50O-NR-ID-SECU    TO CO-IDPRKB-STOCK  OF VMBWCEF      00023900
024000     MOVE BC50O-NS-SEQ-IRMO   TO NS-IRMO-STOCK    OF VMBWCEF      00024000
024100     MOVE BC50O-DA-UBSEC-ISSU TO DA-UBSECIS-STOCK OF VMBWCEF      00024100
024200*                                                                 00024200
024300     OBTAIN CALC VMBWCEF                                          00024300
024400*                                                                 00024400
024500     IF ERROR-STATUS NOT = '0000'                                 00024500
024600        DISPLAY 'VMBWCEF    ' VMBWCEF                             00024600
024700        DISPLAY 'ERROR-STATUS ' ERROR-STATUS                      00024700
024800        DISPLAY ' '                                               00024800
024900     END-IF                                                       00024900
025000     IF ERROR-STATUS = '0000'                                     00025000
025100        OBTAIN FIRST VMBEFF WITHIN VMBWCEF-VMBEFF                 00025100
025200     END-IF                                                       00025200
025300*                                                                 00025300
025400     PERFORM VERWERK-EFFEKT UNTIL ERROR-STATUS NOT = '0000'.      00025400
025500*                                                                 00025500
025600     READ EMISSIONS-I INTO INPUT-RECORD                           00025600
025700        AT END MOVE 1 TO SW-EOF                                   00025700
025800     END-READ.                                                    00025800
025900/                                                                 00025900
026000*-----------------------------------------------------------------00026000
026100 VERWERK-EFFEKT.                                                  00026100
026200*-----------------------------------------------------------------00026200
026300     MOVE 0                 TO LAATSTE-DA-CR-EVENT-PROD.          00026300
026400     MOVE 0                 TO LAATSTE-OPD.                       00026400
026500     MOVE '000000'          TO LAATSTE-CI.                        00026500
026600     MOVE 0                 TO SW-168                             00026600
026700     OBTAIN FIRST VMBEVEF WITHIN VMBEFF-VMBEVEF.                  00026700
026800     PERFORM NEXT-VMBEVEF UNTIL ERROR-STATUS NOT = '0000'.        00026800
026900     IF SW-168 = 1                                                00026900
027000        MOVE LAATSTE-CI         TO UIT-NR-CI                      00027000
027100        MOVE AM-CN-STOCK        TO UIT-AM-CN-STOCK                00027100
027200        MOVE I-CO-INTERNE       TO UIT-CO-INTERNE                 00027200
027300        MOVE NR-ID-STOCK-CD     TO UIT-NR-ID-STOCK-CD             00027300
027400        MOVE BC50O-CO-CURR-SECU TO UIT-CO-DEVISE                  00027400
027500        WRITE REFFEKT-O     FROM UITREC                           00027500
027600     END-IF.                                                      00027600
027700     OBTAIN NEXT VMBEFF WITHIN VMBWCEF-VMBEFF.                    00027700
027800*                                                                 00027800
027900*-----------------------------------------------------------------00027900
028000 NEXT-VMBEVEF.                                                    00028000
028100*-----------------------------------------------------------------00028100
028200     MOVE NR-ID-GOOD TO HULP-NR-ID-GOOD                           00028200
028300     IF CT-RK-TEVPR OF VMBEVEF = '0168' AND                       00028300
028400        CT-OPD = 91 AND                                           00028400
028500        DA-CR-EVENT-PROD < WS-DA-CYMD                             00028500
028600                                                                  00028600
028700        MOVE WS-DA-UE TO WS-DA-UE-MIN-1MAAND                      00028700
028800        IF MM OF WS-DA-UE-MIN-1MAAND < 2                          00028800
028900           MOVE 12      TO MM   OF WS-DA-UE-MIN-1MAAND            00028900
029000           SUBTRACT 1 FROM CCYY OF WS-DA-UE-MIN-1MAAND            00029000
029100        ELSE                                                      00029100
029200           SUBTRACT 1 FROM MM   OF WS-DA-UE-MIN-1MAAND            00029200
029300        END-IF                                                    00029300
029400                                                                  00029400
029500        IF WS-DA-UE-MIN-1MAAND NOT > DA-CR-EVENT-PROD             00029500
029600           MOVE 1 TO SW-168                                       00029600
029700        END-IF                                                    00029700
029800     END-IF.                                                      00029800
029900*                                                                 00029900
030000     IF CT-RK-TEVPR OF VMBEVEF = '0060' AND                       00030000
030100        DA-CR-EVENT-PROD NOT < WS-DA-CYMD                         00030100
030200        CONTINUE                                                  00030200
030300     ELSE                                                         00030300
030400        IF CT-RK-TEVPR OF VMBEVEF   = '0060' AND                  00030400
030500           LAATSTE-DA-CR-EVENT-PROD = 0                           00030500
030600           MOVE 1                 TO LAATSTE-DA-CR-EVENT-PROD     00030600
030700           MOVE NR-CI             TO LAATSTE-CI                   00030700
030800           MOVE CT-OPD            TO LAATSTE-OPD                  00030800
030900        ELSE                                                      00030900
031000           IF CT-RK-TEVPR OF VMBEVEF = '0092' AND                 00031000
031100              HULP-DA-UB-TRANSF > LAATSTE-DA-CR-EVENT-PROD AND    00031100
031200              HULP-DA-UB-TRANSF < WS-DA-CYMD-N                    00031200
031300              MOVE HULP-DA-UB-TRANSF TO LAATSTE-DA-CR-EVENT-PROD  00031300
031400              MOVE NR-CI             TO LAATSTE-CI                00031400
031500           END-IF                                                 00031500
031600        END-IF                                                    00031600
031700     END-IF                                                       00031700
031800*                                                                 00031800
031900     OBTAIN NEXT VMBEVEF WITHIN VMBEFF-VMBEVEF.                   00031900
032000*-----------------------------------------------------------------00032000
032100 CALL-VM9BC50T.                                                   00032100
032200*-----------------------------------------------------------------00032200
032300     INITIALIZE WS-VM9BC50I.                                      00032300
032400     INITIALIZE WS-VM9BC50O.                                      00032400
032500     MOVE 'VM4BD302'       TO BC50I-NM-CALLER                     00032500
032600     MOVE 'VM9BC50T'       TO BC50I-NM-BB                         00032600
032700     MOVE 'P'              TO BC50I-CO-TRANSMISSION               00032700
032800     MOVE 'QUERY001'       TO BC50I-NM-FUNCTION                   00032800
032900     MOVE '2'              TO BC50I-CO-CLE                        00032900
033000     MOVE I-CO-INTERNE     TO BC50I-NR-CLE-NO-INTERNE             00033000
033100     MOVE 'Y'              TO BC50I-CO-DONNEES-FIXES.             00033100
033200     MOVE 'Y'              TO BC50I-CO-CONDITIONS-EMISSION.       00033200
033300     MOVE 'Y'              TO BC50I-CO-CONDITIONS-VENTE.          00033300
033400     MOVE WS-DA-CYMD       TO BC50I-DA-DEMANDE.                   00033400
033500     MOVE WS-VM9BC50I      TO WS-VM9BC50T.                        00033500
033600     CALL CS-VM9BC50T USING WS-VM9BC50T.                          00033600
033700     MOVE WS-VM9BC50T      TO WS-VM9BC50O.                        00033700
