000100 CBL NOSQL                                                        00000100
000200 IDENTIFICATION DIVISION.                                         00000200
000300*========================                                         00000300
000400 PROGRAM-ID. VM4BD310.                                            00000400
000500                                                                  00000500
000600 AUTHOR. VHEML. 2006/03.                                          00000600
000700*                                                                 00000700
000800*  OPZOEKEN GEGEVENS MAANDELIJKSE MUTATIES VIA ACCESS             00000800
000900*  IDMS DB OMLOOP/CIRCULATIE                                      00000900
001000*                                                                 00001000
001100                                                                  00001100
001110******************************************************************00001110
001120* WIJZIGINGEN :                                                  *00001120
001121*                                                                *00001121
001130* TERMA : 11/03/2009 P27                                         *00001130
001140* NIEUWE ZONE OLD-CI TOEGEVOEGD IN INPUT-FILE +                  *00001140
001150* DEZE ZONE OLD-CI MOVEN NAAR NR-CIINPTR-OORD VAN VMBD510I       *00001150
001160******************************************************************00001160
001170                                                                  00001170
001200 ENVIRONMENT DIVISION.                                            00001200
001300*=====================                                            00001300
001400 CONFIGURATION SECTION.                                           00001400
001500*----------------------                                           00001500
001600 SOURCE-COMPUTER. ES9000.                                         00001600
001700 OBJECT-COMPUTER. ES9000.                                         00001700
001800 SPECIAL-NAMES.                                                   00001800
001900     DECIMAL-POINT IS COMMA.                                      00001900
002000                                                                  00002000
002100 INPUT-OUTPUT SECTION.                                            00002100
002200*---------------------                                            00002200
002300 FILE-CONTROL.                                                    00002300
002400     SELECT FI-MUTATIES         ASSIGN TO UT-S-DD010.             00002400
002500     SELECT FO-MUTATIES         ASSIGN TO UT-S-DD100.             00002500
002600                                                                  00002600
002700 IDMS-CONTROL SECTION.                                            00002700
002800*----------------------                                           00002800
002900 PROTOCOL. MODE IS BATCH-AUTOSTATUS DEBUG                         00002900
003000           IDMS-RECORDS WITHIN WORKING-STORAGE SECTION.           00003000
003100                                                                  00003100
003200                                                                  00003200
003300 DATA DIVISION.                                                   00003300
003400*==============                                                   00003400
003500 SCHEMA SECTION.                                                  00003500
003600*---------------                                                  00003600
003700 DB  VMBTS07 WITHIN VMBTSCH.                                      00003700
003800                                                                  00003800
003900 FILE SECTION.                                                    00003900
004000*-------------                                                    00004000
004100 FD  FI-MUTATIES                                                  00004100
004200     LABEL RECORD IS STANDARD                                     00004200
004300     RECORDING F                                                  00004300
004400     BLOCK CONTAINS 0.                                            00004400
004500 01  FI-MUTATIES-REC          PIC  X(21).                         00004500
004600*                                                                 00004600
004700 FD  FO-MUTATIES                                                  00004700
004800     LABEL RECORD IS STANDARD                                     00004800
004900     RECORDING F                                                  00004900
005000     BLOCK CONTAINS 0.                                            00005000
005100 01  FO-MUTATIES-REC            PIC  X(1500).                     00005100
005200*                                                                 00005200
005300 WORKING-STORAGE SECTION.                                         00005300
005400*------------------------                                         00005400
005500* -- DATE PARM --                                                 00005500
005600 01  W-DATE              PIC 9(8).                                00005600
005700 01  W-DATE-X REDEFINES W-DATE.                                   00005700
005800     05  W-DATE-Y        PIC 9(4).                                00005800
005900     05  W-DATE-M        PIC 9(2).                                00005900
006000     05  W-DATE-D        PIC 9(2).                                00006000
006100                                                                  00006100
006200 01  VOLGNUMMER                 PIC 9(07) VALUE ZEROES.           00006200
006300 01  COUNT-TREATED              PIC 9(15) VALUE ZEROES.           00006300
006400                                                                  00006400
006500 01  WS-NR-ISSUE.                                                 00006500
006600     03  WS-NR-ID-ISSUE PIC X(7).                                 00006600
006700     03  WS-NR-CD-ISSUE PIC X(2).                                 00006700
006800                                                                  00006800
006900* -- CLE DU FORMULAIRE --                                         00006900
007000 01  WS-NR-ID-GOOD.                                               00007000
007100     03  WS-NR-CIO              PIC 9(8)    COMP-3.               00007100
007200     03  WS-DA-CREA             PIC 9(8)    COMP-3.               00007200
007300     03  WS-NR-ID               PIC 9(6)    COMP-3.               00007300
007400     03  WS-CT-OPD              PIC 999     COMP-3.               00007400
007500     03  WS-CT-OPG              PIC 999     COMP-3.               00007500
007600     03  FILLER                 PIC XX      VALUE SPACES.         00007600
007700                                                                  00007700
007800 01  WS-MUTATIES.                                                 00007800
007900     03 WS-IN-NR-TIT-BC PIC X(13).                                00007900
008000     03 WS-NR-SUITE     PIC X(2).                                 00008000
008010     03 WS-OLD-CI       PIC X(6).                                 00008010
008100                                                                  00008100
008200* ----- USERABEN -----                                            00008200
008300 01  USERABEN                   PIC X(8) VALUE 'USERABEN'.        00008300
008400                                                                  00008400
008500 01  CS-VM4BD310                PIC X(8) VALUE 'VM4BD310'.        00008500
008600                                                                  00008600
008700*---------------------------------------------------------------* 00008700
008800*--- COPYBOOKS                                                    00008800
008900*---------------------------------------------------------------* 00008900
009000     COPY VMBD510I.                                               00009000
009100                                                                  00009100
009200     COPY VMBD05.                                                 00009200
009300                                                                  00009300
009400*---------------------------------------------------------------* 00009400
009500*--- SWITCHES                                                     00009500
009600*---------------------------------------------------------------* 00009600
009700 01  SW-MUTATIES-EOF            PIC X.                            00009700
009800     88 MUTATIES-NOT-EOF                  VALUE 'N'.              00009800
009900     88 MUTATIES-EOF                      VALUE 'Y'.              00009900
010000                                                                  00010000
010100                                                                  00010100
010200 LINKAGE SECTION.                                                 00010200
010300*----------------                                                 00010300
010400 01  LS-PARM-INPUT.                                               00010400
010500     02  LS-PARM                PIC S9(004) COMP.                 00010500
010600     02  LS-PARAM-IND           PIC X.                            00010600
010700     02  LS-DATE8               PIC  9(008).                      00010700
010800                                                                  00010800
010900                                                                  00010900
011000 PROCEDURE DIVISION USING LS-PARM-INPUT.                          00011000
011100*=======================================                          00011100
011200 MAIN.                                                            00011200
011300*-----                                                            00011300
011400     PERFORM INIT-TREATMENT                                       00011400
011500     PERFORM TREAT-MUTATIES UNTIL MUTATIES-EOF                    00011500
011600     PERFORM END-TREATMENT                                        00011600
011700     STOP RUN                                                     00011700
011800     .                                                            00011800
011900                                                                  00011900
012000*----------------------------------------------------------------*00012000
012100 INIT-TREATMENT.                                                  00012100
012200*---------------                                                  00012200
012300     OPEN INPUT  FI-MUTATIES                                      00012300
012400          OUTPUT FO-MUTATIES                                      00012400
012500     SET MUTATIES-NOT-EOF TO TRUE.                                00012500
012600                                                                  00012600
012700* -- BINDS VOOR IDMS                                              00012700
012800     BIND RUN-UNIT                                                00012800
012900     ON ANY-ERROR-STATUS                                          00012900
013000       PERFORM IDMS-STATUS.                                       00013000
013100                                                                  00013100
013200     BIND VMBEFF                                                  00013200
013300     ON ANY-ERROR-STATUS                                          00013300
013400       PERFORM IDMS-STATUS.                                       00013400
013500                                                                  00013500
013600     BIND VMBEVEF                                                 00013600
013700     ON ANY-ERROR-STATUS                                          00013700
013800       PERFORM IDMS-STATUS.                                       00013800
013900                                                                  00013900
014000* -- READY                                                        00014000
014100     READY AR-VMBEFF1 USAGE-MODE IS RETRIEVAL                     00014100
014200     ON ANY-ERROR-STATUS                                          00014200
014300       PERFORM IDMS-STATUS.                                       00014300
014400                                                                  00014400
014500     PERFORM READ-MUTATIES                                        00014500
014600     .                                                            00014600
014700                                                                  00014700
014800*----------------------------------------------------------------*00014800
014900 END-TREATMENT.                                                   00014900
015000*--------------                                                   00015000
015100* -- FINISH                                                       00015100
015200     FINISH                                                       00015200
015300     ON ANY-ERROR-STATUS                                          00015300
015400       PERFORM IDMS-STATUS.                                       00015400
015500                                                                  00015500
015600     CLOSE FI-MUTATIES                                            00015600
015700           FO-MUTATIES                                            00015700
015800                                                                  00015800
015900     DISPLAY '# TREATED  = ' COUNT-TREATED                        00015900
016000     .                                                            00016000
016100                                                                  00016100
016200*----------------------------------------------------------------*00016200
016300 TREAT-MUTATIES.                                                  00016300
016400*--------------                                                   00016400
016500     PERFORM SEARCH-MUTATIES.                                     00016500
016600     PERFORM MOVE-MUTATIES.                                       00016600
016700     PERFORM WRITE-MUTATIES.                                      00016700
016800     PERFORM READ-MUTATIES                                        00016800
016900     .                                                            00016900
017000                                                                  00017000
017100*----------------------------------------------------------------*00017100
017200 SEARCH-MUTATIES.                                                 00017200
017300*---------------                                                  00017300
017400     MOVE SPACES              TO KY-EFFECT      OF VMBEFF.        00017400
017500     MOVE '1002'              TO CT-RK-TPROD    OF VMBEFF.        00017500
017600     MOVE WS-IN-NR-TIT-BC     TO NR-ID-STOCK-CD OF VMBEFF.        00017600
017700     MOVE WS-NR-SUITE         TO NS-DB-STOCK    OF VMBEFF.        00017700
017800                                                                  00017800
017900*DB2: Expanded LRF FIRST VMBTL07-R01 WHERE ALL-VMBEVEF-BY-VMBEFF  00017900
017900*  -> VMBEVEF WITHIN VMBEFF-VMBEVEF.                              00017900
017900     OBTAIN FIRST VMBEVEF WITHIN VMBEFF-VMBEVEF.                  00017900
018000                                                                  00018000
018100     IF DB-REC-NOT-FOUND                                          00018100
018200        DISPLAY 'VMBEFF NOT FOUND : ' KY-EFFECT OF VMBEFF         00018200
018300        CALL USERABEN                                             00018300
018400     END-IF.                                                      00018400
018500     IF DB-REC-NOT-FOUND                                          00018500
018600        DISPLAY 'VMBEVEF NOT FOUND : ' KY-EFFECT OF VMBEFF        00018600
018700        CALL USERABEN                                             00018700
018800     END-IF.                                                      00018800
018900                                                                  00018900
019000* -- ZOEK DE MUTATIE                                              00019000
019100     PERFORM UNTIL DB-END-OF-SET                                  00019100
019200                OR CT-EVENT OF VMBEVEF = '0092'                   00019200
019300*DB2: Expanded LRF NEXT VMBTL07-R01 WHERE ALL-VMBEVEF-BY-VMBEFF ->00019300
019300*  VMBEVEF WITHIN VMBEFF-VMBEVEF.                                 00019300
019300       OBTAIN NEXT VMBEVEF WITHIN VMBEFF-VMBEVEF.                 00019300
019400     END-PERFORM.                                                 00019400
019500                                                                  00019500
019600     IF DB-END-OF-SET                                             00019600
019700        DISPLAY 'NO MORE VMBEVEF : ' KY-EFFECT OF VMBEFF          00019700
019800        CALL USERABEN                                             00019800
019900     END-IF.                                                      00019900
020000                                                                  00020000
020100*----------------------------------------------------------------*00020100
020200 MOVE-MUTATIES.                                                   00020200
020300*-------------                                                    00020300
020400     INITIALIZE VMBD510I                                          00020400
020500      REPLACING ALPHANUMERIC BY SPACES                            00020500
020600                     NUMERIC BY ZEROES.                           00020600
020700                                                                  00020700
020800     MOVE NR-ID-GOOD OF VMBEVEF TO WS-NR-ID-GOOD.                 00020800
020900                                                                  00020900
021000     MOVE NR-CI               OF VMBEVEF                          00021000
021100       TO NR-CIO-FORM-AS      OF VMBD510I.                        00021100
021200     MOVE WS-DA-CREA                                              00021200
021300       TO DA-CREA-FORM-AS-R   OF VMBD510I.                        00021300
021400     STRING DA-CR-FORM-AS-Y   OF VMBD510I '-'                     00021400
021500            DA-CR-FORM-AS-M   OF VMBD510I '-'                     00021500
021600            DA-CR-FORM-AS-D   OF VMBD510I '-'                     00021600
021700            '01.01.01.000001'                                     00021700
021800            DELIMITED BY SIZE                                     00021800
021900       INTO TS-CREA-OORD      OF VMBD510I.                        00021900
022000     MOVE WS-NR-ID                                                00022000
022100       TO NR-ID-FORM-AS       OF VMBD510I.                        00022100
022200     MOVE WS-CT-OPG                                               00022200
022300       TO CT-OPG-FORM-AS-R    OF VMBD510I.                        00022300
022400     MOVE WS-CT-OPD                                               00022400
022500       TO CT-OPD-FORM-AS-R    OF VMBD510I.                        00022500
022600                                                                  00022600
022700     MOVE NR-ID-ISSUE  OF VMBEFF TO WS-NR-ID-ISSUE                00022700
022800     MOVE NR-CD-ISSUE  OF VMBEFF TO WS-NR-CD-ISSUE                00022800
022900     MOVE WS-NR-ISSUE  TO NR-ISSUIN-OORD    OF VMBD510I.          00022900
023000     MOVE AM-CN-STOCK         OF VMBEFF                           00023000
023100       TO AM-CNS-FORM-AS      OF VMBD510I.                        00023100
023200     MOVE NR-ID-STOCK-CD      OF VMBEFF                           00023200
023300       TO NR-ST-FORM-AS-R     OF VMBD510I.                        00023300
023400     MOVE NR-ID-STOCK-CD      OF VMBEFF                           00023400
023500       TO NR-STIN-OORD        OF VMBD510I.                        00023500
023600     MOVE NS-DB-STOCK         OF VMBEFF                           00023600
023700       TO NS-DBST-OORD        OF VMBD510I.                        00023700
023800     IF NX-CPCRE-STOCK OF VMBEFF = 0                              00023800
023900       MOVE AM-CND-STOCK        OF VMBEFF                         00023900
024000         TO AM-CND-FORM-AS      OF VMBD510I                       00024000
024100     ELSE                                                         00024100
024200       MOVE AM-INTER-STOCK      OF VMBEFF                         00024200
024300         TO AM-INTER-FORM-AS    OF VMBD510I                       00024300
024400     END-IF.                                                      00024400
024500     MOVE CO-IDPRKB-STOCK     OF VMBEFF                           00024500
024600       TO NR-ID-040SECU       OF VMBD510I.                        00024600
024700     MOVE NS-IRMO-STOCK       OF VMBEFF                           00024700
024800       TO NS-SEQ-040IRMO      OF VMBD510I.                        00024800
024900     MOVE DA-UBSECIS-STOCK    OF VMBEFF                           00024900
025000       TO DA-UB-FORM-AS       OF VMBD510I.                        00025000
025100     MOVE DA-CR-EVENT-PROD    OF VMBEVEF                          00025100
025200       TO DA-COMPTABILISATION-OPER OF VMBD510I.                   00025200
025300     MOVE DA-CR-EVENT-PROD    OF VMBEVEF                          00025300
025400       TO DA-EXEC-OORD        OF VMBD510I.                        00025400
025500                                                                  00025500
025600     MOVE NX-CPCRE-STOCK      OF VMBEFF                           00025600
025700       TO NS-RANK-COUP        OF VMBD510I.                        00025700
025800     MOVE NX-CPAID-STOCK      OF VMBEFF                           00025800
025900       TO NX-CPAID-STOCK      OF VMBD510I.                        00025900
026000*    MOVE NX-CPFDU-STOCK      OF VMBEFF                           00026000
026100                                                                  00026100
026200* EXTRA ZONES OPVULLEN                                            00026200
026300                                                                  00026300
026400     EVALUATE WS-CT-OPD                                           00026400
026500       WHEN 00                                                    00026500
026600           MOVE 'MU' TO CO-TYPOPER-OORD OF VMBD510I               00026600
026700       WHEN OTHER                                                 00026700
026800           MOVE '??' TO CO-TYPOPER-OORD OF VMBD510I               00026800
026900           DISPLAY 'ABEND VERKEERDE CT-OPD = '                    00026900
027000                    WS-CT-OPD                                     00027000
027100           DISPLAY  VMBEFF                                        00027100
027200           DISPLAY  VMBEVEF                                       00027200
027300           CALL USERABEN                                          00027300
027400     END-EVALUATE.                                                00027400
027500* UITGIFTE = SRW DUS '1'                                          00027500
027600     MOVE '1' TO CO-ISSUIN-OORD OF VMBD510I.                      00027600
027700     MOVE 001 TO NB-ST-OORD     OF VMBD510I.                      00027700
027800* EFFECT = IKB = DEXIA DUS '1'                                    00027800
027900     MOVE '1' TO CO-STIN-OORD   OF VMBD510I.                      00027900
028000                                                                  00028000
028100     ADD 1 TO VOLGNUMMER.                                         00028100
028200     STRING 'CIR '                                                00028200
028300            CT-OPD-FORM-AS OF VMBD510I ' '                        00028300
028400            VOLGNUMMER                                            00028400
028500            DELIMITED BY SIZE                                     00028500
028600       INTO NR-REFORD-OORD OF VMBD510I.                           00028600
028700                                                                  00028700
028800* EXTRA'S ANNIE STEPPE                                            00028800
028900     STRING 'X'                                                   00028900
029000            '000000'                                              00029000
029100            '      '                                              00029100
029200            DELIMITED BY SIZE                                     00029200
029300       INTO NR-TRANS-OORD  OF VMBD510I.                           00029300
029400* 10=AGENCY 11=ZETEL                                              00029400
029500*    IF NR-CIO-FORM-AS OF VMBD510I =                              00029500
029600*       NR-CIW-FORM-AS OF VMBD510I                                00029600
029700       MOVE '10' TO CO-TYPKAN2-OORD OF VMBD510I                   00029700
029800*    ELSE                                                         00029800
029900*      MOVE '11' TO CO-TYPKAN2-OORD OF VMBD510I                   00029900
030000*    END-IF.                                                      00030000
030100     MOVE 'DX' TO CO-BANK-OORD    OF VMBD510I.                    00030100
030200                                                                  00030200
030210     MOVE WS-OLD-CI TO NR-CIINPTR-OORD OF VMBD510I.               00030210
030220                                                                  00030220
030300*----------------------------------------------------------------*00030300
030400 WRITE-MUTATIES.                                                  00030400
030500*--------------                                                   00030500
030600       ADD 1 TO COUNT-TREATED                                     00030600
030700       WRITE FO-MUTATIES-REC FROM VMBD510I                        00030700
030800     .                                                            00030800
030900                                                                  00030900
031000*----------------------------------------------------------------*00031000
031100 READ-MUTATIES.                                                   00031100
031200*-------------                                                    00031200
031300     READ FI-MUTATIES INTO    WS-MUTATIES                         00031300
031400     AT END                                                       00031400
031500       SET MUTATIES-EOF TO TRUE                                   00031500
031600     NOT AT END                                                   00031600
031700       CONTINUE                                                   00031700
031800     END-READ                                                     00031800
031900     .                                                            00031900
032000                                                                  00032000
032100/---------------------------------------------------------------* 00032100
032200*    ERROR HANDLING                                               00032200
032300*---------------------------------------------------------------* 00032300
032400 IDMS-ABORT.                                                      00032400
032500     EXIT.                                                        00032500
032600     COPY IDMS IDMS-STATUS.                                       00032600
