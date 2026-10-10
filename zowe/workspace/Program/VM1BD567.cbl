000010 CBL NOSQL                                                        00000010
000100 IDENTIFICATION DIVISION.                                         00000100
000200*-----------------------.                                         00000200
000300 PROGRAM-ID.    VM1BD567.                                         00000300
000400 AUTHOR.        D'ANGELO PATRICE.                                 00000400
000500 DATE-WRITTEN.  AOUT 1988.                                        00000500
000600 DATE-COMPILED.                                                   00000600
000700                                                                  00000700
000800****************************************************************  00000800
000900*REMARKS.       AANDUIDEN BOEKING IN DB FORMULIER              *  00000900
001000*               VOOR EFFECTENDOSSIERS.                         *  00001000
001100*                                                              *  00001100
001200*COMMITS        MICHELINE BEEVERS (DATAPROCESS BELGIUM).       *  00001200
001300*                                                              *  00001300
001400*  MODIFIED BY J.CLEMENT                                       *  00001400
001500*  07/92 : AANPASSING SLIK : RECORDS 475 ---> 575              *  00001500
001600*                            VMBD510C    ---> VMBD510V         *  00001600
001700*                                                              *  00001700
001800*  MODIFIED BY S. POMPONIO                                     *  00001800
001900*  01/97 : AANPASSING EURO2000 : RECORDS 750 ---> 1050         *  00001900
002000*                                VMBD510V    ---> VMBD510X     *  00002000
002100*                                DATEPARM EN 8 POSITIONS       *  00002100
002200*                                                              *  00002200
002300*  MODIFIED BY JEROEN "JEROD" DE SCHUTTER (DOLMEN) :           *  00002300
002400*  08/2003 : AANPASSINGEN IKV. INTEGRATIEPROJECT 6212 :        *  00002400
002500*            DAISY SECURITIES KASBONS : VMBD510X --> VMBD205I  *  00002500
002600*                                                              *  00002600
002700****************************************************************  00002700
002800                                                                  00002800
002900 ENVIRONMENT DIVISION.                                            00002900
003000*--------------------.                                            00003000
003100 CONFIGURATION SECTION.                                           00003100
003200 SPECIAL-NAMES.                                                   00003200
003300     DECIMAL-POINT IS COMMA.                                      00003300
003400 INPUT-OUTPUT SECTION.                                            00003400
003500 FILE-CONTROL.                                                    00003500
003600     SELECT OPERATIES ASSIGN TO UT-S-DD010.                       00003600
003700 IDMS-CONTROL SECTION.                                            00003700
003800 PROTOCOL. MODE IS BATCH-AUTOSTATUS DEBUG                         00003800
003900           IDMS-RECORDS WITHIN WORKING-STORAGE SECTION.           00003900
004000                                                                  00004000
004100 DATA DIVISION.                                                   00004100
004200*-------------.                                                   00004200
004300 FILE SECTION.                                                    00004300
004400 FD   OPERATIES                                                   00004400
004500      BLOCK CONTAINS 0 RECORDS                                    00004500
004600      RECORD CONTAINS 1200 CHARACTERS                             00004600
004700      RECORDING F                                                 00004700
004800      LABEL RECORDS STANDARD.                                     00004800
004900 01   OPERATIES-REC             PIC X(1200).                      00004900
005000                                                                  00005000
005100 SCHEMA SECTION.                                                  00005100
005200 DB VMBTS06 WITHIN VMBTSCH.                                       00005200
005300                                                                  00005300
005400 WORKING-STORAGE SECTION.                                         00005400
005500 77  USERABEN                   PIC X(8) VALUE 'USERABEN'.        00005500
005600 77  CTR-REC                    PIC 9(9) COMP-3 VALUE 0.          00005600
005700 77  STOP01                     PIC X(50)                         00005700
005800     VALUE '##&&VM1BD567-STOP01 ACCES DB FORMULAIRE'.             00005800
005900 77  SW-EOF                     PIC X       VALUE 'N'.            00005900
006000 77  SW-RECAB                   PIC X       VALUE 'Y'.            00006000
006100                                                                  00006100
006200 01  STOP-DATONLY.                                                00006200
006300     02  DATE-YMD.                                                00006300
006400         03  D-YEAR             PIC 99.                           00006400
006500         03  D-MONTH            PIC 99.                           00006500
006600         03  D-DAY              PIC 99.                           00006600
006700     02  DATE-DMY.                                                00006700
006800         03  D-DAY              PIC 99.                           00006800
006900         03  D-MONTH            PIC 99.                           00006900
007000         03  D-YEAR             PIC 99.                           00007000
007100     02  DATE-YMD8.                                               00007100
007200         03  D-CENT             PIC 99.                           00007200
007300         03  D-YEAR             PIC 99.                           00007300
007400         03  D-MONTH            PIC 99.                           00007400
007500         03  D-DAY              PIC 99.                           00007500
007600     02  DATE-DMY8.                                               00007600
007700         03  D-DAY              PIC 99.                           00007700
007800         03  D-MONTH            PIC 99.                           00007800
007900         03  D-CENT             PIC 99.                           00007900
008000         03  D-YEAR             PIC 99.                           00008000
008100                                                                  00008100
008200 COPY VMBD205I.                                                   00008200
008300                                                                  00008300
008400 LINKAGE SECTION.                                                 00008400
008500 01  PARAM-DATONLY.                                               00008500
008600     03  L-PARAM                PIC S9(4) COMP.                   00008600
008700     03  DATUMLS.                                                 00008700
008800         05  DATE-IND           PIC X.                            00008800
008900         05  DATE8-LS           PIC X(8).                         00008900
009000                                                                  00009000
009100 PROCEDURE DIVISION USING PARAM-DATONLY.                          00009100
009200*--------------------------------------.                          00009200
009300*                                                                 00009300
009400* INITIALISATIE                                                   00009400
009500*                                                                 00009500
009600     MOVE DATE8-LS       TO DATE-DMY8.                            00009600
009700     MOVE CORR DATE-DMY8 TO DATE-YMD.                             00009700
009800     MOVE CORR DATE-DMY8 TO DATE-DMY.                             00009800
009900     MOVE CORR DATE-DMY8 TO DATE-YMD8.                            00009900
010000                                                                  00010000
010100     MOVE 'VM1BD567' TO PROGRAM-NAME.                             00010100
010200     OPEN INPUT OPERATIES.                                        00010200
010300     COPY IDMS SUBSCHEMA-BINDS                                    00010300
010400     READY USAGE-MODE IS UPDATE.                                  00010400
010500*                                                                 00010500
010600*    RESTART -> RECHERCHE FFRECAB                                 00010600
010700*    SI EXISTE   : REPOSITIONNEMENT SUR LE DERNIER RECORD TRAITE  00010700
010800*    SINON       : CREATION DU RECORD                             00010800
010900*                                                                 00010900
011000     MOVE 'VM1BDF567-A'       TO NM-ID-FF OF FFRECAB.             00011000
011100     MOVE DATE-YMD8           TO DA-CR-FF OF FFRECAB.             00011100
011200     MOVE 0                   TO NS-SET-FF.                       00011200
011300     OBTAIN  CALC FFRECAB                                         00011300
011400          ON DB-REC-NOT-FOUND  MOVE 'N' TO SW-RECAB.              00011400
011500                                                                  00011500
011600     IF SW-RECAB = 'Y'                                            00011600
011700        PERFORM READ-FLAT-FILE                                    00011700
011800                VARYING CTR-REC FROM 1 BY 1                       00011800
011900                UNTIL SW-EOF = 'Y' OR CTR-REC > NS-REC-FF-IN      00011900
012000     ELSE                                                         00012000
012100        MOVE '1'            TO CT-SET-FF OF FFRECAB               00012100
012200        MOVE 'A'            TO CT-REC-FF OF FFRECAB               00012200
012300        MOVE SPACES         TO GR-REC-FF OF FFRECAB               00012300
012400        MOVE 0              TO NR-KY-FF                           00012400
012500        MOVE 0              TO NS-REC-FF-A                        00012500
012600        MOVE 0              TO NS-REC-FF-IN                       00012600
012700        MOVE 7              TO NB-DAY-FF OF FFRECAB               00012700
012800        STORE FFRECAB                                             00012800
012900     END-IF.                                                      00012900
013000                                                                  00013000
013100     IF NOT SW-EOF = 'Y'                                          00013100
013200        PERFORM READ-FLAT-FILE                                    00013200
013300     END-IF.                                                      00013300
013400                                                                  00013400
013500     PERFORM VERWERKING UNTIL SW-EOF = 'Y'.                       00013500
013600                                                                  00013600
013700     FIND CURRENT FFRECAB                                         00013700
013800     ADD CTR-REC TO NS-REC-FF-IN                                  00013800
013900     MODIFY FFRECAB                                               00013900
014000     MOVE 0 TO CTR-REC.                                           00014000
014100     CLOSE OPERATIES.                                             00014100
014200     FINISH.                                                      00014200
014300     STOP RUN.                                                    00014300
014400                                                                  00014400
014500                                                                  00014500
014600 VERWERKING.                                                      00014600
014700*-----------                                                      00014700
014800     MOVE SPACES                    TO VMBFAR                     00014800
014900     MOVE 1815                      TO CT-RK-TGOOD    OF VMBFAR   00014900
015000     MOVE NR-CIO-FORM-AS-R          TO NR-CIO-FORM-AS OF VMBFAR   00015000
015100     MOVE DA-CREA-FORM-AS-R         TO DA-CR-FORM-AS  OF VMBFAR   00015100
015200     MOVE NR-ID-FORM-AS OF VMBD205I TO NR-ID-FORM-AS  OF VMBFAR   00015200
015300     MOVE CT-OPG-FORM-AS-R          TO CT-OPG-FORM-AS OF VMBFAR   00015300
015400     MOVE CT-OPD-FORM-AS-R          TO CT-OPD-FORM-AS OF VMBFAR   00015400
015500     OBTAIN CALC VMBFAR                                           00015500
015600     MOVE DATE-YMD8 TO DA-INFSD-GDIFAR                            00015600
015700     MODIFY VMBFAR.                                               00015700
015800                                                                  00015800
015900*    NA 100 RECORDS EEN COMMIT                                    00015900
016000     IF CTR-REC > 99                                              00016000
016100        FIND CURRENT FFRECAB                                      00016100
016200        ADD CTR-REC TO NS-REC-FF-IN                               00016200
016300        MODIFY FFRECAB                                            00016300
016400        MOVE 0 TO CTR-REC                                         00016400
016500        COMMIT                                                    00016500
016600     END-IF.                                                      00016600
016700                                                                  00016700
016800*    LEZEN VAN DE INVOER                                          00016800
016900     PERFORM READ-FLAT-FILE.                                      00016900
017000                                                                  00017000
017100                                                                  00017100
017200 READ-FLAT-FILE.                                                  00017200
017300*---------------                                                  00017300
017400     READ OPERATIES INTO VMBD205I                                 00017400
017500          AT END MOVE 'Y' TO SW-EOF.                              00017500
017600                                                                  00017600
017700                                                                  00017700
017800 IDMS-ABORT.                                                      00017800
017900     COPY IDMS IDMS-STATUS.                                       00017900
