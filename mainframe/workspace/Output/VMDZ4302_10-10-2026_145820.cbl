000010 CBL ARITH(EXTEND)                                                00010000
000020 IDENTIFICATION DIVISION.                                         00020000
000030*------------------------                                         00030000
000040 PROGRAM-ID. VMDZ4302.                                            00040000
000050 AUTHOR.       Veerapandian.                                      00050000
000060*-----------------------------------------------------------------00060000
000070*         OPHALEN VAN EFFEKTEN MET EVENEMENTEN DIE TERUGBETAALD ZI00070000
000080*         1 MAAND VOOR DE EINDVERVALDAG                           00080000
000090*-----------------------------------------------------------------00090000
000100* 12 NOV 1997 MODIFIED BY PETER VERBEEK                           00100000
000110*             VERWIJDEREN BAREMA DER WAARDEN                      00110000
000120*-----------------------------------------------------------------00120000
000130* 19 JAN 1998 MODIFIED BY PETER VERBEEK                           00130000
000140*             EURO AANPASSINGEN                                   00140000
000150*-----------------------------------------------------------------00150000
000160* 11 DEC 2004 MODIFIED BY NICOLAS JORIS                           00160000
000170*             ADAPTATIONS DAISY SECURITIES SUITE AUX MODIFICATIONS00170000
000180*             DE LA DB.                                           00180000
000190*             CE PROGRAMME EST UNE ADAPTATION DE VM4OM003         00190000
000200*-----------------------------------------------------------------00200000
000210* MODIFIED BY VHEML                                               00210000
000220*   2007/11 : HERCOMPILATIE P20 2767 ENGELS UITTREKSEL            00220000
000230*-----------------------------------------------------------------00230000
000240*                                                                 00240000
000250 DATE-WRITTEN. 2026-10-10.                                        00250000
000260/                                                                 00260000
000270*-----------------------------------------------------------------00270000
000280 ENVIRONMENT DIVISION.                                            00280000
000290*-----------------------------------------------------------------00290000
000300 INPUT-OUTPUT SECTION.                                            00300000
000310 FILE-CONTROL.                                                    00310000
000320     SELECT EMISSIONS-I ASSIGN TO UT-S-DD010.                     00320000
000330     SELECT EFFEKT-O    ASSIGN TO UT-S-DD005.                     00330000
000340*                                                                 00340000
000350/                                                                 00350000
000360*-----------------------------------------------------------------00360000
000370 DATA DIVISION.                                                   00370000
000380*-----------------------------------------------------------------00380000
000390 FILE SECTION.                                                    00390000
000400 FD  EMISSIONS-I                                                  00400000
000410     BLOCK CONTAINS 0 RECORDS                                     00410000
000420     RECORD CONTAINS 40 CHARACTERS                                00420000
000430     RECORDING MODE F                                             00430000
000440     LABEL RECORDS STANDARD.                                      00440000
000450 01  EMISSIONS-I-REC PIC X(40).                                   00450000
000460*                                                                 00460000
000470 FD  EFFEKT-O                                                     00470000
000480     BLOCK CONTAINS 0 RECORDS                                     00480000
000490     RECORD CONTAINS 90 CHARACTERS                                00490000
000500     RECORDING MODE F                                             00500000
000510     LABEL RECORDS STANDARD.                                      00510000
000520 01  REFFEKT-O   PIC X(90).                                       00520000
000530*                                                                 00530000
000540*                                                                 00540000
000550*-----------------------------------------------------------------00550000
000560 WORKING-STORAGE SECTION.                                         00560000
000570*-----------------------------------------------------------------00570000
000580*                                                                 00580000
000590 01  CS-VM9BC50T         PIC X(8)    VALUE 'VM9BC50T'.            00590000
000600 01  WS-VM9BC50I.                                                 00600000
000610     COPY VM9BC50I     REPLACING ==:VM9BC50T:== BY ==BC50I==.     00610000
000620 01  WS-VM9BC50O.                                                 00620000
000630     COPY VM9BC50O     REPLACING ==:VM9BC50T:== BY ==BC50O==.     00630000
000640 01  WS-VM9BC50T.                                                 00640000
000650     05  TE-INTERFACE           PIC  X(001) OCCURS 32000.         00650000
000660 01  INPUT-RECORD.                                                00660000
000670     02  I-CO-INTERNE PIC X(11).                                  00670000
000680     02  I-DA-UB.                                                 00680000
000690         03  DD           PIC 99.                                 00690000
000700         03  MM           PIC 99.                                 00700000
000710         03  CCYY         PIC 9999.                               00710000
000720     02 I-DA-UE.                                                  00720000
000730         03  DD           PIC 99.                                 00730000
000740         03  MM           PIC 99.                                 00740000
000750         03  CCYY         PIC 9999.                               00750000
000760*                                                                 00760000
000770 01  VARIABLES.                                                   00770000
000780     03  WS-DA-UE-MIN-1MAAND.                                     00780000
000790         05 CCYY          PIC 9(4).                               00790000
000800         05 MM            PIC 99.                                 00800000
000810         05 DD            PIC 99.                                 00810000
000820     03  USERABEN                  PIC X(8)    VALUE 'USERABEN'.  00820000
000830     03  SW-EOF                    PIC 9       VALUE 0.           00830000
000840     03  SW-168                    PIC X       VALUE 'N'.         00840000
000850     03  LAATSTE-DA-CR-EVENT-PROD  PIC 9(8)    VALUE 0.           00850000
000860     03  HULP-NR-ID-GOOD.                                         00860000
000870         05  HULP-DA-UB-TRANSF     PIC 9(8)    VALUE ZEROES.      00870000
000880         05  CT-OPD                PIC 9(3)   VALUE ZEROES.       00880000
000890*                                                                 00890000
000900     03  LAATSTE-OPD               PIC 9(3)   VALUE ZEROES.       00900000
000910     03  LAATSTE-CI                PIC X(6)    VALUE '000000'.    00910000
000920 01  UITREC.                                                      00920000
000930     03  UIT-NR-CI            PIC  9(06).                         00930000
000940     03  UIT-AM-CN-STOCK      PIC S9(12)V9(6).                    00940000
000950     03  UIT-CO-DEVISE        PIC  X(03).                         00950000
000960     03  UIT-CO-INTERNE       PIC X(11).                          00960000
000970     03  UIT-NR-ID-STOCK-CD   PIC  9(13).                         00970000
000980*                                                                 00980000
000990 01  ZONE-DATONLY.                                                00990000
001000     02  WS-DA-YMD.                                               01000000
001010         03  YY          PIC 99.                                  01010000
001020         03  MM          PIC 99.                                  01020000
001030         03  DD          PIC 99.                                  01030000
001040*                                                                 01040000
001050     02  WS-DA-DMY.                                               01050000
001060         03  DD          PIC 99.                                  01060000
001070         03  MM          PIC 99.                                  01070000
001080         03  YY          PIC 99.                                  01080000
001090*                                                                 01090000
001100     02  WS-DA-CYMD-N    PIC 9(8).                                01100000
001110     02  WS-DA-CYMD REDEFINES WS-DA-CYMD-N.                       01110000
001120         03  CCYY        PIC 9999.                                01120000
001130         03  MM          PIC 99.                                  01130000
001140         03  DD          PIC 99.                                  01140000
001150*                                                                 01150000
001160     02  WS-DA-UE.                                                01160000
001170         03  CCYY        PIC 9999.                                01170000
001180         03  MM          PIC 99.                                  01180000
001190         03  DD          PIC 99.                                  01190000
001200*                                                                 01200000
001210*-----------------------------------------------------------------01210000
001220                                                                  01220000
001230*DB2 INFRASTRUCTURE - SQLCA, INCLUDES, FLAGS                   *  01230000
001240     EXEC SQL INCLUDE SQLERRWS END-EXEC.                          01240000
001250     EXEC SQL INCLUDE SQLCA END-EXEC.                             01250000
001260     EXEC SQL INCLUDE DZBEFFTV END-EXEC.                          01260000
001270     EXEC SQL INCLUDE DZEVEFTV END-EXEC.                          01270000
001280     EXEC SQL INCLUDE DZWCEFTV END-EXEC.                          01280000
001290                                                                  01290000
001300*DB2 CURSOR END-OF-CURSOR FLAGS                                *  01300000
001310 01  WS-DZBEFFC1-FLAG               PIC X.                        01310000
001320     88  DZBEFFC1-NOT-EOC           VALUE 'N'.                    01320000
001330     88  DZBEFFC1-EOC               VALUE 'Y'.                    01330000
001340                                                                  01340000
001350 01  WS-DZEVEFC1-FLAG               PIC X.                        01350000
001360     88  DZEVEFC1-NOT-EOC           VALUE 'N'.                    01360000
001370     88  DZEVEFC1-EOC               VALUE 'Y'.                    01370000
001380                                                                  01380000
001390                                                                  01390000
001400*DB2 CURSOR DECLARATIONS                                       *  01400000
001410     EXEC SQL                                                     01410000
001420       DECLARE DZBEFFC1 CURSOR WITH HOLD FOR                      01420000
001430       SELECT                                                     01430000
001440         CT_RKTPROD_479BEFF                                       01440000
001450        , NR_IDSTOCK_479BEFF                                      01450000
001460        , NR_CDSTK_479BEFF                                        01460000
001470        , NS_DBSTK_479BEFF                                        01470000
001480       FROM DZBEFFTV                                              01480000
001490       WHERE                                                      01490000
001500         CO_IDISSUS_479WCEF = :DCLDZWCEFTV.CO-IDISSUS-479WCEF     01500000
001510         AND NS_IRMOS_479WCEF = :DCLDZWCEFTV.NS-IRMOS-479WCEF     01510000
001520         AND DA_UBSECIS_479WCEF = :DCLDZWCEFTV.DA-UBSECIS-479WCEF 01520000
001530       FOR READ ONLY                                              01530000
001540       QUERYNO 254                                                01540000
001550     END-EXEC.                                                    01550000
001560                                                                  01560000
001570     EXEC SQL                                                     01570000
001580       DECLARE DZEVEFC1 CURSOR WITH HOLD FOR                      01580000
001590       SELECT                                                     01590000
001600         CT_RKTEVPR_479EVEF                                       01600000
001610        , NR_IDGOOD_479EVEF                                       01610000
001620        , NR_ID_479EVEF                                           01620000
001630       FROM DZEVEFTV                                              01630000
001640       WHERE                                                      01640000
001650         CT_RKTPROD_479BEFF = :DCLDZBEFFTV.CT-RKTPROD-479BEFF     01650000
001660         AND NR_IDSTOCK_479BEFF = :DCLDZBEFFTV.NR-IDSTOCK-479BEFF 01660000
001670         AND NR_CDSTK_479BEFF = :DCLDZBEFFTV.NR-CDSTK-479BEFF     01670000
001680         AND NS_DBSTK_479BEFF = :DCLDZBEFFTV.NS-DBSTK-479BEFF     01680000
001690       ORDER BY                                                   01690000
001700         NR_ID_479EVEF DESC                                       01700000
001710       FOR READ ONLY                                              01710000
001720       QUERYNO 255                                                01720000
001730     END-EXEC.                                                    01730000
001740                                                                  01740000
001750                                                                  01750000
001760*DB2 GENERATED TIMESTAMP AND AUDIT WORKING STORAGE                01760000
001770 77  CS-PROGRAM               PIC X(8)    VALUE 'VMDZ4302'.       01770000
001780 01 WS-TIMESTAMP-FIELDS.                                          01780000
001790     05 TS-SYSTEM.                                                01790000
001800        10  CC                  PIC X(2).                         01800000
001810        10  YY                  PIC X(2).                         01810000
001820        10  MM                  PIC X(2).                         01820000
001830        10  DD                  PIC X(2).                         01830000
001840        10  HH                  PIC X(2).                         01840000
001850        10  MI                  PIC X(2).                         01850000
001860        10  SS                  PIC X(2).                         01860000
001870        10  TT                  PIC X(2).                         01870000
001880        10  FILLER              PIC X(13).                        01880000
001890     05 TS-TIMESTAMP.                                             01890000
001900        10  CC                  PIC X(2).                         01900000
001910        10  YY                  PIC X(2).                         01910000
001920        10  TE-MARKER1          PIC X    VALUE '-'.               01920000
001930        10  MM                  PIC X(2).                         01930000
001940        10  TE-MARKER2          PIC X    VALUE '-'.               01940000
001950        10  DD                  PIC X(2).                         01950000
001960        10  TE-MARKER3          PIC X    VALUE '-'.               01960000
001970        10  HH                  PIC X(2).                         01970000
001980        10  TE-MARKER4          PIC X    VALUE '.'.               01980000
001990        10  MI                  PIC X(2).                         01990000
002000        10  TE-MARKER5          PIC X    VALUE '.'.               02000000
002010        10  SS                  PIC X(2).                         02010000
002020        10  TE-MARKER6          PIC X    VALUE '.'.               02020000
002030        10  TT                  PIC X(2).                         02030000
002040        10  NNNN                PIC 9(04) VALUE 0.                02040000
002050                                                                  02050000
002060                                                                  02060000
002070*DB2 GENERATED ROW COUNTERS                                       02070000
002080 01  WS-DB2-COUNTERS.                                             02080000
002090     10  WS-NB-BEFF-COUNT         PIC 9(7)    COMP-3 VALUE ZEROES.02090000
002100     10  WS-NB-EVEF-COUNT         PIC 9(7)    COMP-3 VALUE ZEROES.02100000
002110 LINKAGE SECTION.                                                 02110000
002120*-----------------------------------------------------------------02120000
002130 01  PARAM-DATONLY.                                               02130000
002140     03  LS-PARAM        PIC S9(4) COMP.                          02140000
002150     03  LS-DATE-IND     PIC X.                                   02150000
002160     03  LS-DA-DMY.                                               02160000
002170         05  DD          PIC 99.                                  02170000
002180         05  MM          PIC 99.                                  02180000
002190         05  YY          PIC 99.                                  02190000
002200/                                                                 02200000
002210*-----------------------------------------------------------------02210000
002220 PROCEDURE DIVISION USING PARAM-DATONLY.                          02220000
002230 100-INITIALIZE.                                                  02230000
002240*DB2: Centralized initialization (all DCLGEN groups, constants, ti02240000
002250*DB2: Redundant INITIALIZE block removed (consolidated in 100-INIT02250000
002260     MOVE CS-PROGRAM   TO PROGRAM-NAME.                           02260000
002270     PERFORM 600-GET-TIMESTAMP.                                   02270000
002280     .                                                            02280000
002290                                                                  02290000
002300                                                                  02300000
002310*-----------------------------------------------------------------02310000
002320*                                                                 02320000
002330* BEGINVERWERKING                                                 02330000
002340*                                                                 02340000
002350     PERFORM 600-GET-TIMESTAMP.                                   02350000
002360     IF LS-DATE-IND = '0'                                         02360000
002370        ACCEPT WS-DA-YMD FROM DATE                                02370000
002380        MOVE CORR WS-DA-YMD TO WS-DA-DMY                          02380000
002390     ELSE                                                         02390000
002400        MOVE LS-DA-DMY TO WS-DA-DMY                               02400000
002410     END-IF                                                       02410000
002420     MOVE CORR WS-DA-DMY TO WS-DA-CYMD.                           02420000
002430     MOVE YY OF WS-DA-DMY TO CCYY OF WS-DA-CYMD.                  02430000
002440*                                                                 02440000
002450     IF CCYY OF WS-DA-CYMD LESS 80                                02450000
002460        ADD 2000 TO CCYY OF WS-DA-CYMD                            02460000
002470     ELSE                                                         02470000
002480        ADD 1900 TO CCYY OF WS-DA-CYMD                            02480000
002490     END-IF                                                       02490000
002500*                                                                 02500000
002510     MOVE 'VMDZ4302' TO PROGRAM-NAME.                             02510000
002520     IF ERROR-STATUS NOT = '0000'                                 02520000
002530        DISPLAY 'BIND RUN-UNIT MISLUKT '                          02530000
002540        DISPLAY 'ERROR-STATUS ' ERROR-STATUS                      02540000
002550        CALL USERABEN                                             02550000
002560     END-IF                                                       02560000
002570     IF ERROR-STATUS NOT = '0000'                                 02570000
002580        DISPLAY 'BIND VMBWCEF MISLUKT '                           02580000
002590        DISPLAY 'ERROR-STATUS ' ERROR-STATUS                      02590000
002600        CALL USERABEN                                             02600000
002610     END-IF                                                       02610000
002620     IF ERROR-STATUS NOT = '0000'                                 02620000
002630        DISPLAY 'BIND VMBEFF  MISLUKT '                           02630000
002640        DISPLAY 'ERROR-STATUS ' ERROR-STATUS                      02640000
002650        CALL USERABEN                                             02650000
002660     END-IF                                                       02660000
002670     IF ERROR-STATUS NOT = '0000'                                 02670000
002680        DISPLAY 'BIND VMBEVEF MISLUKT '                           02680000
002690        DISPLAY 'ERROR-STATUS ' ERROR-STATUS                      02690000
002700        CALL USERABEN                                             02700000
002710     END-IF                                                       02710000
002720     IF ERROR-STATUS NOT = '0000'                                 02720000
002730        DISPLAY 'READY AREA VMBEFF1 MISLUKT '                     02730000
002740        DISPLAY 'ERROR-STATUS ' ERROR-STATUS                      02740000
002750        CALL USERABEN                                             02750000
002760     END-IF                                                       02760000
002770     IF ERROR-STATUS NOT = '0000'                                 02770000
002780        DISPLAY 'READY AREA VMBWCEF MISLUKT '                     02780000
002790        DISPLAY 'ERROR-STATUS ' ERROR-STATUS                      02790000
002800        CALL USERABEN                                             02800000
002810     END-IF                                                       02810000
002820*                                                                 02820000
002830     OPEN INPUT  EMISSIONS-I                                      02830000
002840     OUTPUT EFFEKT-O.                                             02840000
002850*                                                                 02850000
002860     READ EMISSIONS-I INTO INPUT-RECORD                           02860000
002870        AT END MOVE 1 TO SW-EOF                                   02870000
002880     END-READ.                                                    02880000
002890*                                                                 02890000
002900     PERFORM VERWERK-EMISSIONS UNTIL SW-EOF = 1.                  02900000
002910*                                                                 02910000
002920     CLOSE EMISSIONS-I.                                           02920000
002930 EFFEKT-O.                                                        02930000
002940*                                                                 02940000
002950*DB2: COMMIT removed; retrieval program is read-only.             02950000
002960     DISPLAY 'TOTAL BEFF RECORDS   : ' WS-NB-BEFF-COUNT           02960000
002970     DISPLAY 'TOTAL EVEF RECORDS   : ' WS-NB-EVEF-COUNT           02970000
002980                                                                  02980000
002990     STOP RUN.                                                    02990000
003000 600-GET-TIMESTAMP.                                               03000000
003010     MOVE FUNCTION CURRENT-DATE            TO TS-SYSTEM.          03010000
003020     MOVE CC OF TS-SYSTEM             TO CC OF TS-TIMESTAMP       03020000
003030     MOVE YY OF TS-SYSTEM             TO YY OF TS-TIMESTAMP       03030000
003040     MOVE MM OF TS-SYSTEM             TO MM OF TS-TIMESTAMP       03040000
003050     MOVE DD OF TS-SYSTEM             TO DD OF TS-TIMESTAMP       03050000
003060     MOVE HH OF TS-SYSTEM             TO HH OF TS-TIMESTAMP       03060000
003070     MOVE MI OF TS-SYSTEM             TO MI OF TS-TIMESTAMP       03070000
003080     MOVE SS OF TS-SYSTEM             TO SS OF TS-TIMESTAMP       03080000
003090     MOVE TT OF TS-SYSTEM             TO TT OF TS-TIMESTAMP       03090000
003100     DISPLAY 'TIMESTAMP: ' TS-TIMESTAMP                           03100000
003110     .                                                            03110000
003120                                                                  03120000
003130/                                                                 03130000
003140*-----------------------------------------------------------------03140000
003150 VERWERK-EMISSIONS.                                               03150000
003160*-----------------------------------------------------------------03160000
003170     MOVE CORR I-DA-UE TO WS-DA-UE                                03170000
003180     PERFORM CALL-VM9BC50T                                        03180000
003190     MOVE BC50O-NR-ID-SECU    TO CO-IDISSUS-479WCEF OF DCLDZWCEFTV03190000
003200     MOVE BC50O-NS-SEQ-IRMO   TO NS-IRMOS-479WCEF OF DCLDZWCEFTV  03200000
003210     MOVE BC50O-DA-UBSEC-ISSU TO DA-UBSECIS-479WCEF OF DCLDZWCEFTV03210000
003220*                                                                 03220000
003230*                                                                 03230000
003240     IF ERROR-STATUS NOT = '0000'                                 03240000
003250        DISPLAY 'VMBWCEF    ' VMBWCEF                             03250000
003260        DISPLAY 'ERROR-STATUS ' ERROR-STATUS                      03260000
003270        DISPLAY ' '                                               03270000
003280     END-IF                                                       03280000
003290     IF ERROR-STATUS = '0000'                                     03290000
003300*DB2: Converted OBTAIN FIRST VMBEFF WITHIN VMBWCEF-VMBEFF.        03300000
003310        PERFORM 710-OPEN-DZBEFFC1.                                03310000
003320        PERFORM 720-FETCH-DZBEFFC1.                               03320000
003330     END-IF                                                       03330000
003340*                                                                 03340000
003350     PERFORM VERWERK-EFFEKT UNTIL ERROR-STATUS NOT = '0000'.      03350000
003360     PERFORM 730-CLOSE-DZBEFFC1.                                  03360000
003370*                                                                 03370000
003380     READ EMISSIONS-I INTO INPUT-RECORD                           03380000
003390        AT END MOVE 1 TO SW-EOF                                   03390000
003400     END-READ.                                                    03400000
003410/                                                                 03410000
003420*-----------------------------------------------------------------03420000
003430 VERWERK-EFFEKT.                                                  03430000
003440*-----------------------------------------------------------------03440000
003450     MOVE 0                 TO LAATSTE-DA-CR-EVENT-PROD.          03450000
003460     MOVE 0                 TO LAATSTE-OPD.                       03460000
003470     MOVE '000000'          TO LAATSTE-CI.                        03470000
003480     MOVE 0                 TO SW-168                             03480000
003490*DB2: Converted OBTAIN FIRST VMBEVEF WITHIN VMBEFF-VMBEVEF.       03490000
003500     PERFORM 810-OPEN-DZEVEFC1.                                   03500000
003510     PERFORM 820-FETCH-DZEVEFC1.                                  03510000
003520     PERFORM NEXT-VMBEVEF UNTIL ERROR-STATUS NOT = '0000'.        03520000
003530     PERFORM 830-CLOSE-DZEVEFC1.                                  03530000
003540     IF SW-168 = 1                                                03540000
003550        MOVE LAATSTE-CI         TO UIT-NR-CI                      03550000
003560        MOVE AM-CN-STOCK        TO UIT-AM-CN-STOCK                03560000
003570        MOVE I-CO-INTERNE       TO UIT-CO-INTERNE                 03570000
003580        MOVE NR-ID-STOCK-CD     TO UIT-NR-ID-STOCK-CD             03580000
003590        MOVE BC50O-CO-CURR-SECU TO UIT-CO-DEVISE                  03590000
003600        WRITE REFFEKT-O     FROM UITREC                           03600000
003610     END-IF.                                                      03610000
003620*DB2: Converted OBTAIN NEXT VMBEFF WITHIN VMBWCEF-VMBEFF.         03620000
003630     PERFORM 720-FETCH-DZBEFFC1.                                  03630000
003640*                                                                 03640000
003650*-----------------------------------------------------------------03650000
003660 NEXT-VMBEVEF.                                                    03660000
003670*-----------------------------------------------------------------03670000
003680     MOVE NR-IDGOOD-479EVEF OF DCLDZEVEFTV TO HULP-NR-ID-GOOD     03680000
003690     IF CT-RKTEVPR-479EVEF OF DCLDZEVEFTV = '0168' AND            03690000
003700        CT-OPD = 91 AND DA-CR-EVENT-PROD < WS-DA-CYMD             03700000
003710                                                                  03710000
003720        MOVE WS-DA-UE TO WS-DA-UE-MIN-1MAAND                      03720000
003730        IF MM OF WS-DA-UE-MIN-1MAAND < 2                          03730000
003740           MOVE 12      TO MM   OF WS-DA-UE-MIN-1MAAND            03740000
003750           SUBTRACT 1 FROM CCYY OF WS-DA-UE-MIN-1MAAND            03750000
003760        ELSE                                                      03760000
003770           SUBTRACT 1 FROM MM   OF WS-DA-UE-MIN-1MAAND            03770000
003780        END-IF                                                    03780000
003790                                                                  03790000
003800        IF WS-DA-UE-MIN-1MAAND NOT > DA-CR-EVENT-PROD             03800000
003810           MOVE 1 TO SW-168                                       03810000
003820        END-IF                                                    03820000
003830     END-IF.                                                      03830000
003840*                                                                 03840000
003850     IF CT-RKTEVPR-479EVEF OF DCLDZEVEFTV = '0060' AND            03850000
003860        DA-CR-EVENT-PROD NOT < WS-DA-CYMD                         03860000
003870        CONTINUE                                                  03870000
003880     ELSE                                                         03880000
003890        IF CT-RKTEVPR-479EVEF OF DCLDZEVEFTV   = '0060' AND       03890000
003900           LAATSTE-DA-CR-EVENT-PROD = 0                           03900000
003910           MOVE 1                 TO LAATSTE-DA-CR-EVENT-PROD     03910000
003920           MOVE NR-CI             TO LAATSTE-CI                   03920000
003930           MOVE CT-OPD            TO LAATSTE-OPD                  03930000
003940        ELSE                                                      03940000
003950           IF CT-RKTEVPR-479EVEF OF DCLDZEVEFTV = '0092' AND      03950000
003960              HULP-DA-UB-TRANSF > LAATSTE-DA-CR-EVENT-PROD AND    03960000
003970              HULP-DA-UB-TRANSF < WS-DA-CYMD-N                    03970000
003980              MOVE HULP-DA-UB-TRANSF TO LAATSTE-DA-CR-EVENT-PROD  03980000
003990              MOVE NR-CI             TO LAATSTE-CI                03990000
004000           END-IF                                                 04000000
004010        END-IF                                                    04010000
004020     END-IF                                                       04020000
004030*                                                                 04030000
004040*DB2: Converted OBTAIN NEXT VMBEVEF WITHIN VMBEFF-VMBEVEF.        04040000
004050     PERFORM 820-FETCH-DZEVEFC1.                                  04050000
004060*-----------------------------------------------------------------04060000
004070 CALL-VM9BC50T.                                                   04070000
004080*-----------------------------------------------------------------04080000
004090     INITIALIZE WS-VM9BC50I.                                      04090000
004100     INITIALIZE WS-VM9BC50O.                                      04100000
004110     MOVE 'VM4BD302'       TO BC50I-NM-CALLER                     04110000
004120     MOVE 'VM9BC50T'       TO BC50I-NM-BB                         04120000
004130     MOVE 'P'              TO BC50I-CO-TRANSMISSION               04130000
004140     MOVE 'QUERY001'       TO BC50I-NM-FUNCTION                   04140000
004150     MOVE '2'              TO BC50I-CO-CLE                        04150000
004160     MOVE I-CO-INTERNE     TO BC50I-NR-CLE-NO-INTERNE             04160000
004170     MOVE 'Y'              TO BC50I-CO-DONNEES-FIXES.             04170000
004180     MOVE 'Y'              TO BC50I-CO-CONDITIONS-EMISSION.       04180000
004190     MOVE 'Y'              TO BC50I-CO-CONDITIONS-VENTE.          04190000
004200     MOVE WS-DA-CYMD       TO BC50I-DA-DEMANDE.                   04200000
004210     MOVE WS-VM9BC50I      TO WS-VM9BC50T.                        04210000
004220     CALL CS-VM9BC50T USING WS-VM9BC50T.                          04220000
004230     MOVE WS-VM9BC50T      TO WS-VM9BC50O.                        04230000
004240                                                                  04240000
004250*DB2 GENERATED CURSOR OPEN FETCH CLOSE PARAGRAPHS              *  04250000
004260                                                                  04260000
004270 710-OPEN-DZBEFFC1.                                               04270000
004280D    DISPLAY '710-OPEN-DZBEFFC1.'                                 04280000
004290     MOVE 710    TO SQL-LOCATION                                  04290000
004300                                                                  04300000
004310     EXEC SQL                                                     04310000
004320       OPEN DZBEFFC1                                              04320000
004330     END-EXEC                                                     04330000
004340                                                                  04340000
004350     EVALUATE SQLCODE                                             04350000
004360       WHEN ZERO                                                  04360000
004370            SET DZBEFFC1-NOT-EOC TO TRUE                          04370000
004380       WHEN OTHER                                                 04380000
004390            MOVE 710    TO SQL-LOCATION                           04390000
004400            DISPLAY 'ERROR WHILE OPENING CURSOR DZBEFFC1'         04400000
004410            PERFORM SQLERROR                                      04410000
004420     END-EVALUATE                                                 04420000
004430     .                                                            04430000
004440                                                                  04440000
004450 720-FETCH-DZBEFFC1.                                              04450000
004460D    DISPLAY '720-FETCH-DZBEFFC1.'                                04460000
004470     SET DZBEFFC1-NOT-EOC TO TRUE                                 04470000
004480     MOVE 720    TO SQL-LOCATION                                  04480000
004490                                                                  04490000
004500     EXEC SQL                                                     04500000
004510       FETCH DZBEFFC1                                             04510000
004520       INTO :DCLDZBEFFTV.CT-RKTPROD-479BEFF                       04520000
004530       , :DCLDZBEFFTV.NR-IDSTOCK-479BEFF                          04530000
004540       , :DCLDZBEFFTV.NR-CDSTK-479BEFF                            04540000
004550       , :DCLDZBEFFTV.NS-DBSTK-479BEFF                            04550000
004560     END-EXEC                                                     04560000
004570                                                                  04570000
004580     EVALUATE SQLCODE                                             04580000
004590       WHEN ZERO                                                  04590000
004600            ADD 1 TO WS-NB-BEFF-COUNT                             04600000
004610            CONTINUE                                              04610000
004620       WHEN 100                                                   04620000
004630            SET DZBEFFC1-EOC TO TRUE                              04630000
004640       WHEN OTHER                                                 04640000
004650            MOVE 720    TO SQL-LOCATION                           04650000
004660            DISPLAY 'ERROR WHILE FETCHING CURSOR DZBEFFC1'        04660000
004670            DISPLAY 'CT-RKTPROD-479BEFF : ' CT-RKTPROD-479BEFF    04670000
004680            OF DCLDZBEFFTV                                        04680000
004690            DISPLAY 'NR-IDSTOCK-479BEFF : ' NR-IDSTOCK-479BEFF    04690000
004700            OF DCLDZBEFFTV                                        04700000
004710            DISPLAY 'NR-CDSTK-479BEFF   : ' NR-CDSTK-479BEFF      04710000
004720            OF DCLDZBEFFTV                                        04720000
004730            DISPLAY 'NS-DBSTK-479BEFF   : ' NS-DBSTK-479BEFF      04730000
004740            OF DCLDZBEFFTV                                        04740000
004750            PERFORM SQLERROR                                      04750000
004760     END-EVALUATE                                                 04760000
004770     .                                                            04770000
004780                                                                  04780000
004790 730-CLOSE-DZBEFFC1.                                              04790000
004800D    DISPLAY '730-CLOSE-DZBEFFC1.'                                04800000
004810     MOVE 730    TO SQL-LOCATION                                  04810000
004820                                                                  04820000
004830     EXEC SQL                                                     04830000
004840       CLOSE DZBEFFC1                                             04840000
004850     END-EXEC                                                     04850000
004860                                                                  04860000
004870     EVALUATE SQLCODE                                             04870000
004880       WHEN ZERO                                                  04880000
004890            CONTINUE                                              04890000
004900       WHEN OTHER                                                 04900000
004910            MOVE 730    TO SQL-LOCATION                           04910000
004920            DISPLAY 'ERROR WHILE CLOSING CURSOR DZBEFFC1'         04920000
004930            PERFORM SQLERROR                                      04930000
004940     END-EVALUATE                                                 04940000
004950     .                                                            04950000
004960                                                                  04960000
004970 810-OPEN-DZEVEFC1.                                               04970000
004980D    DISPLAY '810-OPEN-DZEVEFC1.'                                 04980000
004990     MOVE 810    TO SQL-LOCATION                                  04990000
005000                                                                  05000000
005010     EXEC SQL                                                     05010000
005020       OPEN DZEVEFC1                                              05020000
005030     END-EXEC                                                     05030000
005040                                                                  05040000
005050     EVALUATE SQLCODE                                             05050000
005060       WHEN ZERO                                                  05060000
005070            SET DZEVEFC1-NOT-EOC TO TRUE                          05070000
005080       WHEN OTHER                                                 05080000
005090            MOVE 810    TO SQL-LOCATION                           05090000
005100            DISPLAY 'ERROR WHILE OPENING CURSOR DZEVEFC1'         05100000
005110            PERFORM SQLERROR                                      05110000
005120     END-EVALUATE                                                 05120000
005130     .                                                            05130000
005140                                                                  05140000
005150 820-FETCH-DZEVEFC1.                                              05150000
005160D    DISPLAY '820-FETCH-DZEVEFC1.'                                05160000
005170     SET DZEVEFC1-NOT-EOC TO TRUE                                 05170000
005180     MOVE 820    TO SQL-LOCATION                                  05180000
005190                                                                  05190000
005200     EXEC SQL                                                     05200000
005210       FETCH DZEVEFC1                                             05210000
005220       INTO :DCLDZEVEFTV.CT-RKTEVPR-479EVEF                       05220000
005230       , :DCLDZEVEFTV.NR-IDGOOD-479EVEF                           05230000
005240       , :DCLDZEVEFTV.NR-ID-479EVEF                               05240000
005250     END-EXEC                                                     05250000
005260                                                                  05260000
005270     EVALUATE SQLCODE                                             05270000
005280       WHEN ZERO                                                  05280000
005290            ADD 1 TO WS-NB-EVEF-COUNT                             05290000
005300            CONTINUE                                              05300000
005310       WHEN 100                                                   05310000
005320            SET DZEVEFC1-EOC TO TRUE                              05320000
005330       WHEN OTHER                                                 05330000
005340            MOVE 820    TO SQL-LOCATION                           05340000
005350            DISPLAY 'ERROR WHILE FETCHING CURSOR DZEVEFC1'        05350000
005360            DISPLAY 'CT-RKTEVPR-479EVEF : ' CT-RKTEVPR-479EVEF    05360000
005370            OF DCLDZEVEFTV                                        05370000
005380            DISPLAY 'NR-IDGOOD-479EVEF  : ' NR-IDGOOD-479EVEF     05380000
005390            OF DCLDZEVEFTV                                        05390000
005400            DISPLAY 'NR-ID-479EVEF      : ' NR-ID-479EVEF         05400000
005410            OF DCLDZEVEFTV                                        05410000
005420            PERFORM SQLERROR                                      05420000
005430     END-EVALUATE                                                 05430000
005440     .                                                            05440000
005450                                                                  05450000
005460 830-CLOSE-DZEVEFC1.                                              05460000
005470D    DISPLAY '830-CLOSE-DZEVEFC1.'                                05470000
005480     MOVE 830    TO SQL-LOCATION                                  05480000
005490                                                                  05490000
005500     EXEC SQL                                                     05500000
005510       CLOSE DZEVEFC1                                             05510000
005520     END-EXEC                                                     05520000
005530                                                                  05530000
005540     EVALUATE SQLCODE                                             05540000
005550       WHEN ZERO                                                  05550000
005560            CONTINUE                                              05560000
005570       WHEN OTHER                                                 05570000
005580            MOVE 830    TO SQL-LOCATION                           05580000
005590            DISPLAY 'ERROR WHILE CLOSING CURSOR DZEVEFC1'         05590000
005600            PERFORM SQLERROR                                      05600000
005610     END-EVALUATE                                                 05610000
005620     .                                                            05620000
005630                                                                  05630000
005640*SQLERROR ROUTINE.                                                05640000
005650     EXEC SQL                                                     05650000
005660       INCLUDE SQLERROR                                           05660000
005670     END-EXEC.                                                    05670000
