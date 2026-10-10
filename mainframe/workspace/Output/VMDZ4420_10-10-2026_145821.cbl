000010 CBL ARITH(EXTEND)                                                00010000
000020 IDENTIFICATION DIVISION.                                         00020000
000030*------------------------                                         00030000
000040 PROGRAM-ID. VMDZ4420.                                            00040000
000050 AUTHOR.       Veerapandian.                                      00050000
000060 DATE-WRITTEN. 2026-10-10.                                        00060000
000070*                                                                 00070000
000080******************************************************************00080000
000090*                                                                *00090000
000100*                INFORMATORISCHE KASBON 2.                       *00100000
000110*                                                                *00110000
000120******************************************************************00120000
000130*                                                                *00130000
000140*                VERGELIJKING DATABASE EN INVENTARIS             *00140000
000150*                -----------------------------------             *00150000
000160*                                                                *00160000
000170*                TWEEDE PROGRAMMA :                              *00170000
000180*                                                                *00180000
000190*                OPZOEKEN VAN ALLE EFFECTEN EN ALLE EVENEMENTEN  *00190000
000200*                DIE NOG IN LEVEN ZIJN.                          *00200000
000210*                                                                *00210000
000220* 01/06/92 : DE SCHEPPER KOEN (HCS AS) - PROBLEM RECORD 436451   *00220000
000230*            WAARDEN DIE NOG IN STOCK ZIJN MOGEN NIET MEEGENOMEN *00230000
000240*            WORDEN IN HET OUTPUTBESTAND.                        *00240000
000250*                                                                *00250000
000260* 16/06/92 : DE SCHEPPER KOEN (HCS AS) - PROBLEM RECORD 436451   *00260000
000270*            BIJVOEGEN PARMDATE + TEST OP DA-CRE-EVENT-PROD      *00270000
000280*                                                                *00280000
000290* 12/03/97 : HEYSE K. (SOFT GUIDE)                               *00290000
000300*            AANPASSINGEN EURO EN 2000                           *00300000
000310*            UITBREIDEN BEDRAGEN                                 *00310000
000320*            UITBREIDEN JAARTAL TOT 4 POS VOOR 2000              *00320000
000330*                                                                *00330000
000340* 04/03/98 : DE SCHEPPER KOEN - PROJECT 5421 : TESTWAARDEN       *00340000
000350*            CI CREATIE MEE DOORGEVEN NAAR VERVOLG OM DE         *00350000
000360*            SPLITSING TEST-REEEL TE KUNNEN DOEN                 *00360000
000370* J-M BOOGAERTS                                                  *00370000
000380 000380* 2004/12 REPRENDRE N° DE TITRE EN OUTPUT (12 POS DE LIBRES00380000
000390*                                                                *00390000
000400*                                                                *00400000
000410******************************************************************00410000
000420/                                                                 00420000
000430 ENVIRONMENT DIVISION.                                            00430000
000440*---------------------                                            00440000
000450 INPUT-OUTPUT SECTION.                                            00450000
000460 FILE-CONTROL.                                                    00460000
000470     SELECT UITBST ASSIGN TO UT-S-DD005.                          00470000
000480/                                                                 00480000
000490 DATA DIVISION.                                                   00490000
000500*--------------                                                   00500000
000510 FILE SECTION.                                                    00510000
000520*                                                                 00520000
000530 FD  UITBST                                                       00530000
000540     BLOCK CONTAINS 0 RECORDS                                     00540000
000550     RECORD CONTAINS 50 CHARACTERS                                00550000
000560     RECORDING MODE F                                             00560000
000570     LABEL RECORDS STANDARD.                                      00570000
000580 01  UITRECORD.                                                   00580000
000590     03  UIT-AM-CN-STOCK          PIC S9(13)V99 COMP-3.           00590000
000600     03  UIT-AM-CND-STOCK         PIC S9(13)V99 COMP-3.           00600000
000610     03  UIT-NR-CIO-CRE           PIC 9(6).                       00610000
000620     03  UIT-NR-ID                PIC X(04).                      00620000
000630     03  UIT-NS-SEQ               PIC 9(04).                      00630000
000640     03  UIT-DA-UBSEC             PIC X(08).                      00640000
000650     03  UIT-NR-ST                PIC X(12).                      00650000
000660*                                                                 00660000
000670*                                                                 00670000
000680 WORKING-STORAGE SECTION.                                         00680000
000690*                                                                 00690000
000700 01  WS-TE-WORK.                                                  00700000
000710     10  WS-STATUS                PIC X    VALUE SPACE.           00710000
000720     10  SW-STATUS-D              PIC X    VALUE 'N'.             00720000
000730     10  USERABEN                 PIC X(8) VALUE 'USERABEN'.      00730000
000740     10  WS-NR-ID-GOOD.                                           00740000
000750         20  WS-NR-CIO-CRE        PIC 9(8) VALUE ZEROES.          00750000
000760         20  WS-DA-CR-CRE         PIC 9(8) VALUE ZEROES.          00760000
000770         20  WS-NR-ID-CRE         PIC 9(6) VALUE ZEROES.          00770000
000780         20  WS-CT-OPD-CRE        PIC 9(3) VALUE ZEROES.          00780000
000790         20  WS-CT-OPG-CRE        PIC 9(3) VALUE ZEROES.          00790000
000800*                                                                 00800000
000810*----- FIELDS ESDATMAS ------------------------------------------*00810000
000820     COPY ESDATMAS.                                               00820000
000830*----- FIELDS PARAMETER DATE ------------------------------------*00830000
000840 01  ZONE-DATONLY.                                                00840000
000850     03  DATE6R-WS.                                               00850000
000860         05  D-YEAR               PIC 99.                         00860000
000870         05  D-MONTH              PIC 99.                         00870000
000880         05  D-DAY                PIC 99.                         00880000
000890     03  DATE6 REDEFINES DATE6R-WS.                               00890000
000900         05  D-DAY                PIC 99.                         00900000
000910         05  D-MONTH              PIC 99.                         00910000
000920         05  D-YEAR               PIC 99.                         00920000
000930     03  DATE8.                                                   00930000
000940         05  D-DAY                PIC 99.                         00940000
000950         05  D-MONTH              PIC 99.                         00950000
000960         05  D-CENT               PIC 99.                         00960000
000970         05  D-YEAR               PIC 99.                         00970000
000980     03  PARMDATE.                                                00980000
000990         05  D-YEAR               PIC 9(4).                       00990000
001000         05  D-MONTH              PIC 9(2).                       01000000
001010         05  D-DAY                PIC 9(2).                       01010000
001020*                                                                 01020000
001030                                                                  01030000
001040*DB2 INFRASTRUCTURE - SQLCA, INCLUDES, FLAGS                   *  01040000
001050     EXEC SQL INCLUDE SQLERRWS END-EXEC.                          01050000
001060     EXEC SQL INCLUDE SQLCA END-EXEC.                             01060000
001070     EXEC SQL INCLUDE DZBEFFTV END-EXEC.                          01070000
001080     EXEC SQL INCLUDE DZEVEFTV END-EXEC.                          01080000
001090                                                                  01090000
001100*DB2 CURSOR END-OF-CURSOR FLAGS                                *  01100000
001110 01  WS-DZBEFFC1-FLAG               PIC X.                        01110000
001120     88  DZBEFFC1-NOT-EOC           VALUE 'N'.                    01120000
001130     88  DZBEFFC1-EOC               VALUE 'Y'.                    01130000
001140                                                                  01140000
001150 01  WS-DZEVEFC1-FLAG               PIC X.                        01150000
001160     88  DZEVEFC1-NOT-EOC           VALUE 'N'.                    01160000
001170     88  DZEVEFC1-EOC               VALUE 'Y'.                    01170000
001180                                                                  01180000
001190                                                                  01190000
001200*DB2 CURSOR DECLARATIONS                                       *  01200000
001210     EXEC SQL                                                     01210000
001220       DECLARE DZBEFFC1 CURSOR WITH HOLD FOR                      01220000
001230       SELECT                                                     01230000
001240         AM_CNDSTK_479BEFF                                        01240000
001250        , AM_CNSTK_479BEFF                                        01250000
001260        , CO_IDPRKSK_479BEFF                                      01260000
001270        , DA_UBSECIS_479BEFF                                      01270000
001280        , NR_IDSTOCK_479BEFF                                      01280000
001290        , NS_IRMOSTK_479BEFF                                      01290000
001300        , CT_RKTPROD_479BEFF                                      01300000
001310        , NR_CDSTK_479BEFF                                        01310000
001320        , NS_DBSTK_479BEFF                                        01320000
001330       FROM DZBEFFTV                                              01330000
001340       FOR READ ONLY                                              01340000
001350       QUERYNO 254                                                01350000
001360     END-EXEC.                                                    01360000
001370                                                                  01370000
001380     EXEC SQL                                                     01380000
001390       DECLARE DZEVEFC1 CURSOR WITH HOLD FOR                      01390000
001400       SELECT                                                     01400000
001410         CO_STEVPRN_479EVEF                                       01410000
001420        , CT_RKTEVPR_479EVEF                                      01420000
001430        , DA_CREVTPD_479EVEF                                      01430000
001440        , NR_IDGOOD_479EVEF                                       01440000
001450        , NR_ID_479EVEF                                           01450000
001460       FROM DZEVEFTV                                              01460000
001470       WHERE                                                      01470000
001480         CT_RKTPROD_479BEFF = :DCLDZBEFFTV.CT-RKTPROD-479BEFF     01480000
001490         AND NR_IDSTOCK_479BEFF = :DCLDZBEFFTV.NR-IDSTOCK-479BEFF 01490000
001500         AND NR_CDSTK_479BEFF = :DCLDZBEFFTV.NR-CDSTK-479BEFF     01500000
001510         AND NS_DBSTK_479BEFF = :DCLDZBEFFTV.NS-DBSTK-479BEFF     01510000
001520       ORDER BY                                                   01520000
001530         NR_ID_479EVEF DESC                                       01530000
001540       FOR READ ONLY                                              01540000
001550       QUERYNO 255                                                01550000
001560     END-EXEC.                                                    01560000
001570                                                                  01570000
001580*DB2 DATE CONVERSION WORKING STORAGE                              01580000
001590 01  WS-DATUMVELDEN.                                              01590000
001600     03  DA-CCYYMMDD.                                             01600000
001610         05  CC                    PIC 99       VALUE ZERO.       01610000
001620         05  YY                    PIC 99       VALUE ZERO.       01620000
001630         05  MM                    PIC 99       VALUE ZERO.       01630000
001640         05  DD                    PIC 99       VALUE ZERO.       01640000
001650     03  DA-CCYYMMDD-R REDEFINES DA-CCYYMMDD.                     01650000
001660         05  CCYY                  PIC 9999.                      01660000
001670         05  MM                    PIC 99.                        01670000
001680         05  DD                    PIC 99.                        01680000
001690     03  DA-DD-MM-CCYY.                                           01690000
001700         05  DD                    PIC 9(02).                     01700000
001710         05  TE-MARKER5            PIC X        VALUE '.'.        01710000
001720         05  MM                    PIC 9(02).                     01720000
001730         05  TE-MARKER6            PIC X        VALUE '.'.        01730000
001740         05  CCYY                  PIC 9(04).                     01740000
001750     02  HELP-DA-CREVTPD-479EVEF        PIC 9(8)     VALUE ZEROES.01750000
001760                                                                  01760000
001770                                                                  01770000
001780*DB2 GENERATED TIMESTAMP AND AUDIT WORKING STORAGE                01780000
001790 77  CS-PROGRAM               PIC X(8)    VALUE 'VMDZ4420'.       01790000
001800 01 WS-TIMESTAMP-FIELDS.                                          01800000
001810     05 TS-SYSTEM.                                                01810000
001820        10  CC                  PIC X(2).                         01820000
001830        10  YY                  PIC X(2).                         01830000
001840        10  MM                  PIC X(2).                         01840000
001850        10  DD                  PIC X(2).                         01850000
001860        10  HH                  PIC X(2).                         01860000
001870        10  MI                  PIC X(2).                         01870000
001880        10  SS                  PIC X(2).                         01880000
001890        10  TT                  PIC X(2).                         01890000
001900        10  FILLER              PIC X(13).                        01900000
001910     05 TS-TIMESTAMP.                                             01910000
001920        10  CC                  PIC X(2).                         01920000
001930        10  YY                  PIC X(2).                         01930000
001940        10  TE-MARKER1          PIC X    VALUE '-'.               01940000
001950        10  MM                  PIC X(2).                         01950000
001960        10  TE-MARKER2          PIC X    VALUE '-'.               01960000
001970        10  DD                  PIC X(2).                         01970000
001980        10  TE-MARKER3          PIC X    VALUE '-'.               01980000
001990        10  HH                  PIC X(2).                         01990000
002000        10  TE-MARKER4          PIC X    VALUE '.'.               02000000
002010        10  MI                  PIC X(2).                         02010000
002020        10  TE-MARKER5          PIC X    VALUE '.'.               02020000
002030        10  SS                  PIC X(2).                         02030000
002040        10  TE-MARKER6          PIC X    VALUE '.'.               02040000
002050        10  TT                  PIC X(2).                         02050000
002060        10  NNNN                PIC 9(04) VALUE 0.                02060000
002070                                                                  02070000
002080                                                                  02080000
002090*DB2 GENERATED ROW COUNTERS                                       02090000
002100 01  WS-DB2-COUNTERS.                                             02100000
002110     10  WS-NB-BEFF-COUNT         PIC 9(7)    COMP-3 VALUE ZEROES.02110000
002120     10  WS-NB-EVEF-COUNT         PIC 9(7)    COMP-3 VALUE ZEROES.02120000
002130 LINKAGE SECTION.                                                 02130000
002140 01  PARAM-DATONLY.                                               02140000
002150     03  L-PARAM                  PIC S9(4) COMP.                 02150000
002160     03  DATUMLS.                                                 02160000
002170         05  DATE-IND             PIC X.                          02170000
002180         05  DATE8-LS             PIC X(8).                       02180000
002190     EJECT                                                        02190000
002200 PROCEDURE DIVISION USING PARAM-DATONLY.                          02200000
002210 100-INITIALIZE.                                                  02210000
002220*DB2: Centralized initialization (all DCLGEN groups, constants, ti02220000
002230*DB2: Redundant INITIALIZE block removed (consolidated in 100-INIT02230000
002240     MOVE CS-PROGRAM   TO PROGRAM-NAME.                           02240000
002250     PERFORM 600-GET-TIMESTAMP.                                   02250000
002260     .                                                            02260000
002270                                                                  02270000
002280                                                                  02280000
002290*                                                                 02290000
002300* INITIALISATIE                                                   02300000
002310*                                                                 02310000
002320     PERFORM 600-GET-TIMESTAMP.                                   02320000
002330     IF DATE-IND = '0'                                            02330000
002340        ACCEPT DATE6R-WS FROM DATE                                02340000
002350        MOVE CORR DATE6R-WS      TO DATE8                         02350000
002360        IF D-YEAR OF DATE8 > 60                                   02360000
002370           MOVE 19 TO D-CENT OF DATE8                             02370000
002380        ELSE MOVE 20 TO D-CENT OF DATE8                           02380000
002390        END-IF                                                    02390000
002400        MOVE CORR DATE8          TO DATE6                         02400000
002410     ELSE                                                         02410000
002420        MOVE DATE8-LS            TO DATE8                         02420000
002430        MOVE CORR DATE8          TO DATE6                         02430000
002440     END-IF.                                                      02440000
002450     MOVE  DATE6                 TO ES-DATUM.                     02450000
002460     MOVE  ZEROES                TO ES-DAGEN, ES-TYPE-DAG.        02460000
002470     MOVE  '+'                   TO ES-PLUS-MIN.                  02470000
002480*                                                                 02480000
002490     CALL ESDATMAS USING ES-DATUM ES-DAGEN ES-TYPE-DAG ES-PLUS-MIN02490000
002500     ES-ANTWOORD ES-RETURN-CODE ES-WERKZONE.                      02500000
002510*                                                                 02510000
002520     IF ES-RETURN-CODE = '0'                                      02520000
002530        MOVE ES-JJJJ             TO D-YEAR OF PARMDATE            02530000
002540        MOVE ES-MM               TO D-MONTH OF PARMDATE           02540000
002550        MOVE ES-DD               TO D-DAY  OF PARMDATE            02550000
002560     ELSE DISPLAY '***********************************'           02560000
002570        DISPLAY ' '                                               02570000
002580        DISPLAY 'PARAMETER DATE IN ERROR = ' DATE6                02580000
002590        DISPLAY ' '                                               02590000
002600        DISPLAY '***********************************'             02600000
002610        CALL USERABEN                                             02610000
002620     END-IF.                                                      02620000
002630*                                                                 02630000
002640     MOVE 'VMDZ4420' TO PROGRAM-NAME.                             02640000
002650     OPEN OUTPUT UITBST.                                          02650000
002660                                                                  02660000
002670*DB2: Converted OBTAIN FIRST VMBEFF WITHIN AR-VMBEFF1.            02670000
002680     PERFORM 710-OPEN-DZBEFFC1.                                   02680000
002690     PERFORM 720-FETCH-DZBEFFC1 UNTIL DZBEFFC1-EOC.               02690000
002700     PERFORM 730-CLOSE-DZBEFFC1.                                  02700000
002710*                                                                 02710000
002720* HOOFDVERWERKING                                                 02720000
002730*                                                                 02730000
002740*                                                                 02740000
002750* EINDVERWERKING                                                  02750000
002760*                                                                 02760000
002770     CLOSE UITBST.                                                02770000
002780*DB2: COMMIT removed; retrieval program is read-only.             02780000
002790     DISPLAY 'TOTAL BEFF RECORDS   : ' WS-NB-BEFF-COUNT           02790000
002800     DISPLAY 'TOTAL EVEF RECORDS   : ' WS-NB-EVEF-COUNT           02800000
002810                                                                  02810000
002820     STOP RUN.                                                    02820000
002830 600-GET-TIMESTAMP.                                               02830000
002840     MOVE FUNCTION CURRENT-DATE            TO TS-SYSTEM.          02840000
002850     MOVE CC OF TS-SYSTEM             TO CC OF TS-TIMESTAMP       02850000
002860     MOVE YY OF TS-SYSTEM             TO YY OF TS-TIMESTAMP       02860000
002870     MOVE MM OF TS-SYSTEM             TO MM OF TS-TIMESTAMP       02870000
002880     MOVE DD OF TS-SYSTEM             TO DD OF TS-TIMESTAMP       02880000
002890     MOVE HH OF TS-SYSTEM             TO HH OF TS-TIMESTAMP       02890000
002900     MOVE MI OF TS-SYSTEM             TO MI OF TS-TIMESTAMP       02900000
002910     MOVE SS OF TS-SYSTEM             TO SS OF TS-TIMESTAMP       02910000
002920     MOVE TT OF TS-SYSTEM             TO TT OF TS-TIMESTAMP       02920000
002930     DISPLAY 'TIMESTAMP: ' TS-TIMESTAMP                           02930000
002940     .                                                            02940000
002950                                                                  02950000
002960/                                                                 02960000
002970 HOOFDVERWERKING.                                                 02970000
002980*                                                                 02980000
002990* OPZOEKEN VAN ALLE EVENEMENTEN BIJ EEN EFFECT                    02990000
003000*                                                                 03000000
003010     MOVE SPACE TO WS-STATUS                                      03010000
003020*DB2: Converted OBTAIN FIRST VMBEVEF WITHIN VMBEFF-VMBEVEF.       03020000
003030     PERFORM 810-OPEN-DZEVEFC1.                                   03030000
003040     MOVE 'N' TO SW-STATUS-D                                      03040000
003050     PERFORM 820-FETCH-DZEVEFC1 UNTIL DZEVEFC1-EOC OR             03050000
003060     SW-STATUS-D = 'Y'                                            03060000
003070     PERFORM 830-CLOSE-DZEVEFC1.                                  03070000
003080*                                                                 03080000
003090* OPZOEKEN VAN VOLGEND EFFECT IN DE AREA                          03090000
003100*                                                                 03100000
003110*DB2: Removed redundant OBTAIN NEXT after cursor EOC loop.        03110000
003120     CONTINUE.                                                    03120000
003130*                                                                 03130000
003140 VERWERK-VMBEVEF.                                                 03140000
003150*DB2: realigned 1 DB2 DATE host(s) before comparison.             03150000
003160     MOVE ZEROES TO DA-CCYYMMDD                                   03160000
003170     MOVE ZEROES TO HELP-DA-CREVTPD-479EVEF                       03170000
003180     MOVE DA-CREVTPD-479EVEF OF DCLDZEVEFTV TO DA-DD-MM-CCYY      03180000
003190     EVALUATE TRUE                                                03190000
003200       WHEN DA-DD-MM-CCYY = '01.01.0001'                          03200000
003210            MOVE ZEROES TO DA-CCYYMMDD-R                          03210000
003220       WHEN DA-DD-MM-CCYY = '31.12.9999'                          03220000
003230            MOVE '99999999' TO DA-CCYYMMDD-R                      03230000
003240       WHEN OTHER                                                 03240000
003250            MOVE CCYY OF DA-DD-MM-CCYY TO CCYY OF DA-CCYYMMDD-R   03250000
003260            MOVE MM   OF DA-DD-MM-CCYY TO MM   OF DA-CCYYMMDD-R   03260000
003270            MOVE DD   OF DA-DD-MM-CCYY TO DD   OF DA-CCYYMMDD-R   03270000
003280     END-EVALUATE                                                 03280000
003290     MOVE DA-CCYYMMDD-R TO HELP-DA-CREVTPD-479EVEF                03290000
003300     IF HELP-DA-CREVTPD-479EVEF NOT > PARMDATE                    03300000
003310        IF CT-RKTEVPR-479EVEF OF DCLDZEVEFTV = '0060' AND         03310000
003320           WS-STATUS NOT = 'D'                                    03320000
003330           MOVE 'C' TO WS-STATUS                                  03330000
003340           MOVE NR-IDGOOD-479EVEF OF DCLDZEVEFTV TO               03340000
003350           WS-NR-ID-GOOD                                          03350000
003360        ELSE                                                      03360000
003370           IF CT-RKTEVPR-479EVEF OF DCLDZEVEFTV = '0168' AND      03370000
003380              CO-STEVPRN-479EVEF OF DCLDZEVEFTV NOT = '1'         03380000
003390              MOVE 'D' TO WS-STATUS                               03390000
003400              MOVE 'Y' TO SW-STATUS-D                             03400000
003410           ELSE                                                   03410000
003420              IF CT-RKTEVPR-479EVEF OF DCLDZEVEFTV = '0217'       03420000
003430                 AND WS-STATUS = SPACE                            03430000
003440                 MOVE 'S' TO WS-STATUS                            03440000
003450              END-IF                                              03450000
003460           END-IF                                                 03460000
003470        END-IF                                                    03470000
003480     END-IF.                                                      03480000
003490* DB2: Removed redundant SQLCODE wrapper after cursor EOC loop.   03490000
003500     IF WS-STATUS = 'C'                                           03500000
003510        MOVE AM-CNSTK-479BEFF OF DCLDZBEFFTV TO                   03510000
003520        UIT-AM-CN-STOCK                                           03520000
003530        MOVE AM-CNDSTK-479BEFF OF DCLDZBEFFTV TO                  03530000
003540        UIT-AM-CND-STOCK                                          03540000
003550        INITIALIZE UITRECORD                                      03550000
003560        MOVE WS-NR-CIO-CRE TO UIT-NR-CIO-CRE                      03560000
003570        MOVE CO-IDPRKSK-479BEFF OF DCLDZBEFFTV TO                 03570000
003580        UIT-NR-ID                                                 03580000
003590        MOVE NS-IRMOSTK-479BEFF OF DCLDZBEFFTV TO                 03590000
003600        UIT-NS-SEQ                                                03600000
003610        MOVE DA-UBSECIS-479BEFF OF DCLDZBEFFTV TO                 03610000
003620        UIT-DA-UBSEC                                              03620000
003630        MOVE NR-IDSTOCK-479BEFF OF DCLDZBEFFTV TO                 03630000
003640        UIT-NR-ST                                                 03640000
003650        WRITE UITRECORD                                           03650000
003660     END-IF.                                                      03660000
003670/                                                                 03670000
003680                                                                  03680000
003690*DB2 GENERATED CURSOR OPEN FETCH CLOSE PARAGRAPHS              *  03690000
003700                                                                  03700000
003710 710-OPEN-DZBEFFC1.                                               03710000
003720D    DISPLAY '710-OPEN-DZBEFFC1.'                                 03720000
003730     MOVE 710    TO SQL-LOCATION                                  03730000
003740                                                                  03740000
003750     EXEC SQL                                                     03750000
003760       OPEN DZBEFFC1                                              03760000
003770     END-EXEC                                                     03770000
003780                                                                  03780000
003790     EVALUATE SQLCODE                                             03790000
003800       WHEN ZERO                                                  03800000
003810            SET DZBEFFC1-NOT-EOC TO TRUE                          03810000
003820       WHEN OTHER                                                 03820000
003830            MOVE 710    TO SQL-LOCATION                           03830000
003840            DISPLAY 'ERROR WHILE OPENING CURSOR DZBEFFC1'         03840000
003850            PERFORM SQLERROR                                      03850000
003860     END-EVALUATE                                                 03860000
003870     .                                                            03870000
003880                                                                  03880000
003890 720-FETCH-DZBEFFC1.                                              03890000
003900D    DISPLAY '720-FETCH-DZBEFFC1.'                                03900000
003910     SET DZBEFFC1-NOT-EOC TO TRUE                                 03910000
003920     MOVE 720    TO SQL-LOCATION                                  03920000
003930                                                                  03930000
003940     EXEC SQL                                                     03940000
003950       FETCH DZBEFFC1                                             03950000
003960       INTO :DCLDZBEFFTV.AM-CNDSTK-479BEFF                        03960000
003970       , :DCLDZBEFFTV.AM-CNSTK-479BEFF                            03970000
003980       , :DCLDZBEFFTV.CO-IDPRKSK-479BEFF                          03980000
003990       , :DCLDZBEFFTV.DA-UBSECIS-479BEFF                          03990000
004000       , :DCLDZBEFFTV.NR-IDSTOCK-479BEFF                          04000000
004010       , :DCLDZBEFFTV.NS-IRMOSTK-479BEFF                          04010000
004020       , :DCLDZBEFFTV.CT-RKTPROD-479BEFF                          04020000
004030       , :DCLDZBEFFTV.NR-CDSTK-479BEFF                            04030000
004040       , :DCLDZBEFFTV.NS-DBSTK-479BEFF                            04040000
004050     END-EXEC                                                     04050000
004060                                                                  04060000
004070     EVALUATE SQLCODE                                             04070000
004080       WHEN ZERO                                                  04080000
004090            ADD 1 TO WS-NB-BEFF-COUNT                             04090000
004100            CONTINUE                                              04100000
004110       WHEN 100                                                   04110000
004120            SET DZBEFFC1-EOC TO TRUE                              04120000
004130       WHEN OTHER                                                 04130000
004140            MOVE 720    TO SQL-LOCATION                           04140000
004150            DISPLAY 'ERROR WHILE FETCHING CURSOR DZBEFFC1'        04150000
004160            DISPLAY 'AM-CNDSTK-479BEFF  : ' AM-CNDSTK-479BEFF     04160000
004170            OF DCLDZBEFFTV                                        04170000
004180            DISPLAY 'AM-CNSTK-479BEFF   : ' AM-CNSTK-479BEFF      04180000
004190            OF DCLDZBEFFTV                                        04190000
004200            DISPLAY 'CO-IDPRKSK-479BEFF : ' CO-IDPRKSK-479BEFF    04200000
004210            OF DCLDZBEFFTV                                        04210000
004220            DISPLAY 'DA-UBSECIS-479BEFF : ' DA-UBSECIS-479BEFF    04220000
004230            OF DCLDZBEFFTV                                        04230000
004240            DISPLAY 'NR-IDSTOCK-479BEFF : ' NR-IDSTOCK-479BEFF    04240000
004250            OF DCLDZBEFFTV                                        04250000
004260            PERFORM SQLERROR                                      04260000
004270     END-EVALUATE                                                 04270000
004280     .                                                            04280000
004290                                                                  04290000
004300 730-CLOSE-DZBEFFC1.                                              04300000
004310D    DISPLAY '730-CLOSE-DZBEFFC1.'                                04310000
004320     MOVE 730    TO SQL-LOCATION                                  04320000
004330                                                                  04330000
004340     EXEC SQL                                                     04340000
004350       CLOSE DZBEFFC1                                             04350000
004360     END-EXEC                                                     04360000
004370                                                                  04370000
004380     EVALUATE SQLCODE                                             04380000
004390       WHEN ZERO                                                  04390000
004400            CONTINUE                                              04400000
004410       WHEN OTHER                                                 04410000
004420            MOVE 730    TO SQL-LOCATION                           04420000
004430            DISPLAY 'ERROR WHILE CLOSING CURSOR DZBEFFC1'         04430000
004440            PERFORM SQLERROR                                      04440000
004450     END-EVALUATE                                                 04450000
004460     .                                                            04460000
004470                                                                  04470000
004480 810-OPEN-DZEVEFC1.                                               04480000
004490D    DISPLAY '810-OPEN-DZEVEFC1.'                                 04490000
004500     MOVE 810    TO SQL-LOCATION                                  04500000
004510                                                                  04510000
004520     EXEC SQL                                                     04520000
004530       OPEN DZEVEFC1                                              04530000
004540     END-EXEC                                                     04540000
004550                                                                  04550000
004560     EVALUATE SQLCODE                                             04560000
004570       WHEN ZERO                                                  04570000
004580            SET DZEVEFC1-NOT-EOC TO TRUE                          04580000
004590       WHEN OTHER                                                 04590000
004600            MOVE 810    TO SQL-LOCATION                           04600000
004610            DISPLAY 'ERROR WHILE OPENING CURSOR DZEVEFC1'         04610000
004620            PERFORM SQLERROR                                      04620000
004630     END-EVALUATE                                                 04630000
004640     .                                                            04640000
004650                                                                  04650000
004660 820-FETCH-DZEVEFC1.                                              04660000
004670D    DISPLAY '820-FETCH-DZEVEFC1.'                                04670000
004680     SET DZEVEFC1-NOT-EOC TO TRUE                                 04680000
004690     MOVE 820    TO SQL-LOCATION                                  04690000
004700                                                                  04700000
004710     EXEC SQL                                                     04710000
004720       FETCH DZEVEFC1                                             04720000
004730       INTO :DCLDZEVEFTV.CO-STEVPRN-479EVEF                       04730000
004740       , :DCLDZEVEFTV.CT-RKTEVPR-479EVEF                          04740000
004750       , :DCLDZEVEFTV.DA-CREVTPD-479EVEF                          04750000
004760       , :DCLDZEVEFTV.NR-IDGOOD-479EVEF                           04760000
004770       , :DCLDZEVEFTV.NR-ID-479EVEF                               04770000
004780     END-EXEC                                                     04780000
004790                                                                  04790000
004800     EVALUATE SQLCODE                                             04800000
004810       WHEN ZERO                                                  04810000
004820            ADD 1 TO WS-NB-EVEF-COUNT                             04820000
004830            CONTINUE                                              04830000
004840       WHEN 100                                                   04840000
004850            SET DZEVEFC1-EOC TO TRUE                              04850000
004860       WHEN OTHER                                                 04860000
004870            MOVE 820    TO SQL-LOCATION                           04870000
004880            DISPLAY 'ERROR WHILE FETCHING CURSOR DZEVEFC1'        04880000
004890            DISPLAY 'CO-STEVPRN-479EVEF : ' CO-STEVPRN-479EVEF    04890000
004900            OF DCLDZEVEFTV                                        04900000
004910            DISPLAY 'CT-RKTEVPR-479EVEF : ' CT-RKTEVPR-479EVEF    04910000
004920            OF DCLDZEVEFTV                                        04920000
004930            DISPLAY 'DA-CREVTPD-479EVEF : ' DA-CREVTPD-479EVEF    04930000
004940            OF DCLDZEVEFTV                                        04940000
004950            DISPLAY 'NR-IDGOOD-479EVEF  : ' NR-IDGOOD-479EVEF     04950000
004960            OF DCLDZEVEFTV                                        04960000
004970            DISPLAY 'NR-ID-479EVEF      : ' NR-ID-479EVEF         04970000
004980            OF DCLDZEVEFTV                                        04980000
004990            PERFORM SQLERROR                                      04990000
005000     END-EVALUATE                                                 05000000
005010     .                                                            05010000
005020                                                                  05020000
005030 830-CLOSE-DZEVEFC1.                                              05030000
005040D    DISPLAY '830-CLOSE-DZEVEFC1.'                                05040000
005050     MOVE 830    TO SQL-LOCATION                                  05050000
005060                                                                  05060000
005070     EXEC SQL                                                     05070000
005080       CLOSE DZEVEFC1                                             05080000
005090     END-EXEC                                                     05090000
005100                                                                  05100000
005110     EVALUATE SQLCODE                                             05110000
005120       WHEN ZERO                                                  05120000
005130            CONTINUE                                              05130000
005140       WHEN OTHER                                                 05140000
005150            MOVE 830    TO SQL-LOCATION                           05150000
005160            DISPLAY 'ERROR WHILE CLOSING CURSOR DZEVEFC1'         05160000
005170            PERFORM SQLERROR                                      05170000
005180     END-EVALUATE                                                 05180000
005190     .                                                            05190000
005200                                                                  05200000
005210*SQLERROR ROUTINE.                                                05210000
005220     EXEC SQL                                                     05220000
005230       INCLUDE SQLERROR                                           05230000
005240     END-EXEC.                                                    05240000
