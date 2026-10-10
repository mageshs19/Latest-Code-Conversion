000010 CBL ARITH(EXTEND)                                                00010000
000020 IDENTIFICATION DIVISION.                                         00020000
000030*========================                                         00030000
000040 PROGRAM-ID. VMDZ4310.                                            00040000
000050                                                                  00050000
000060 AUTHOR.       Veerapandian.                                      00060000
000070*                                                                 00070000
000080*  OPZOEKEN GEGEVENS MAANDELIJKSE MUTATIES VIA ACCESS             00080000
000090*  IDMS DB OMLOOP/CIRCULATIE                                      00090000
000100*                                                                 00100000
000110                                                                  00110000
000120******************************************************************00120000
000130* WIJZIGINGEN :                                                  *00130000
000140*                                                                *00140000
000150* TERMA : 11/03/2009 P27                                         *00150000
000160* NIEUWE ZONE OLD-CI TOEGEVOEGD IN INPUT-FILE +                  *00160000
000170* DEZE ZONE OLD-CI MOVEN NAAR NR-CIINPTR-OORD VAN VMBD510I       *00170000
000180******************************************************************00180000
000190                                                                  00190000
000200 ENVIRONMENT DIVISION.                                            00200000
000210*=====================                                            00210000
000220 CONFIGURATION SECTION.                                           00220000
000230*----------------------                                           00230000
000240 SOURCE-COMPUTER. ES9000.                                         00240000
000250 OBJECT-COMPUTER. ES9000.                                         00250000
000260 SPECIAL-NAMES.                                                   00260000
000270     DECIMAL-POINT IS COMMA.                                      00270000
000280                                                                  00280000
000290 INPUT-OUTPUT SECTION.                                            00290000
000300*---------------------                                            00300000
000310 FILE-CONTROL.                                                    00310000
000320     SELECT FI-MUTATIES         ASSIGN TO UT-S-DD010.             00320000
000330     SELECT FO-MUTATIES         ASSIGN TO UT-S-DD100.             00330000
000340                                                                  00340000
000350*----------------------                                           00350000
000360                                                                  00360000
000370                                                                  00370000
000380 DATA DIVISION.                                                   00380000
000390*==============                                                   00390000
000400*---------------                                                  00400000
000410                                                                  00410000
000420 FILE SECTION.                                                    00420000
000430*-------------                                                    00430000
000440 FD  FI-MUTATIES                                                  00440000
000450     LABEL RECORD IS STANDARD                                     00450000
000460     RECORDING F                                                  00460000
000470     BLOCK CONTAINS 0.                                            00470000
000480 01  FI-MUTATIES-REC          PIC  X(21).                         00480000
000490*                                                                 00490000
000500 FD  FO-MUTATIES                                                  00500000
000510     LABEL RECORD IS STANDARD                                     00510000
000520     RECORDING F                                                  00520000
000530     BLOCK CONTAINS 0.                                            00530000
000540 01  FO-MUTATIES-REC            PIC  X(1500).                     00540000
000550*                                                                 00550000
000560 WORKING-STORAGE SECTION.                                         00560000
000570*------------------------                                         00570000
000580* -- DATE PARM --                                                 00580000
000590 01  W-DATE              PIC 9(8).                                00590000
000600 01  W-DATE-X REDEFINES W-DATE.                                   00600000
000610     05  W-DATE-Y        PIC 9(4).                                00610000
000620     05  W-DATE-M        PIC 9(2).                                00620000
000630     05  W-DATE-D        PIC 9(2).                                00630000
000640                                                                  00640000
000650 01  VOLGNUMMER                 PIC 9(07) VALUE ZEROES.           00650000
000660 01  COUNT-TREATED              PIC 9(15) VALUE ZEROES.           00660000
000670                                                                  00670000
000680 01  WS-NR-ISSUE.                                                 00680000
000690     03  WS-NR-ID-ISSUE PIC X(7).                                 00690000
000700     03  WS-NR-CD-ISSUE PIC X(2).                                 00700000
000710                                                                  00710000
000720* -- CLE DU FORMULAIRE --                                         00720000
000730 01  WS-NR-ID-GOOD.                                               00730000
000740     03  WS-NR-CIO              PIC 9(8)    VALUE ZEROES.         00740000
000750     03  WS-DA-CREA             PIC 9(8)    VALUE ZEROES.         00750000
000760     03  WS-NR-ID               PIC 9(6)    VALUE ZEROES.         00760000
000770     03  WS-CT-OPD              PIC 999     VALUE ZEROES.         00770000
000780     03  WS-CT-OPG              PIC 999     VALUE ZEROES.         00780000
000790                                                                  00790000
000800 01  WS-MUTATIES.                                                 00800000
000810     03 WS-IN-NR-TIT-BC PIC X(13).                                00810000
000820     03 WS-NR-SUITE     PIC X(2).                                 00820000
000830     03 WS-OLD-CI       PIC X(6).                                 00830000
000840                                                                  00840000
000850* ----- USERABEN -----                                            00850000
000860 01  USERABEN                   PIC X(8) VALUE 'USERABEN'.        00860000
000870                                                                  00870000
000880 01  CS-VM4BD310                PIC X(8) VALUE 'VM4BD310'.        00880000
000890                                                                  00890000
000900*---------------------------------------------------------------* 00900000
000910*--- COPYBOOKS                                                    00910000
000920*---------------------------------------------------------------* 00920000
000930     COPY VMDZ510I.                                               00930000
000940                                                                  00940000
000950     COPY VMDZ05.                                                 00950000
000960                                                                  00960000
000970*---------------------------------------------------------------* 00970000
000980*--- SWITCHES                                                     00980000
000990*---------------------------------------------------------------* 00990000
001000 01  SW-MUTATIES-EOF            PIC X.                            01000000
001010     88 MUTATIES-NOT-EOF                  VALUE 'N'.              01010000
001020     88 MUTATIES-EOF                      VALUE 'Y'.              01020000
001030                                                                  01030000
001040                                                                  01040000
001050                                                                  01050000
001060*DB2 INFRASTRUCTURE - SQLCA, INCLUDES, FLAGS                   *  01060000
001070     EXEC SQL INCLUDE SQLERRWS END-EXEC.                          01070000
001080     EXEC SQL INCLUDE SQLCA END-EXEC.                             01080000
001090     EXEC SQL INCLUDE DZEVEFTV END-EXEC.                          01090000
001100     EXEC SQL INCLUDE DZBEFFTV END-EXEC.                          01100000
001110                                                                  01110000
001120*DB2 CURSOR END-OF-CURSOR FLAGS                                *  01120000
001130 01  WS-DZEVEFC1-FLAG               PIC X.                        01130000
001140     88  DZEVEFC1-NOT-EOC           VALUE 'N'.                    01140000
001150     88  DZEVEFC1-EOC               VALUE 'Y'.                    01150000
001160                                                                  01160000
001170                                                                  01170000
001180*DB2 CURSOR DECLARATIONS                                       *  01180000
001190     EXEC SQL                                                     01190000
001200       DECLARE DZEVEFC1 CURSOR WITH HOLD FOR                      01200000
001210       SELECT                                                     01210000
001220         DA_CREVTPD_479EVEF                                       01220000
001230        , NR_IDGOOD_479EVEF                                       01230000
001240        , NR_ID_479EVEF                                           01240000
001250       FROM DZEVEFTV                                              01250000
001260       WHERE                                                      01260000
001270         CT_RKTPROD_479BEFF = :DCLDZBEFFTV.CT-RKTPROD-479BEFF     01270000
001280         AND NR_IDSTOCK_479BEFF = :DCLDZBEFFTV.NR-IDSTOCK-479BEFF 01280000
001290         AND NR_CDSTK_479BEFF = :DCLDZBEFFTV.NR-CDSTK-479BEFF     01290000
001300         AND NS_DBSTK_479BEFF = :DCLDZBEFFTV.NS-DBSTK-479BEFF     01300000
001310       ORDER BY                                                   01310000
001320         NR_ID_479EVEF DESC                                       01320000
001330       FOR READ ONLY                                              01330000
001340       QUERYNO 254                                                01340000
001350     END-EXEC.                                                    01350000
001360                                                                  01360000
001370                                                                  01370000
001380*DB2 GENERATED TIMESTAMP AND AUDIT WORKING STORAGE                01380000
001390 77  CS-PROGRAM               PIC X(8)    VALUE 'VMDZ4310'.       01390000
001400 01 WS-TIMESTAMP-FIELDS.                                          01400000
001410     05 TS-SYSTEM.                                                01410000
001420        10  CC                  PIC X(2).                         01420000
001430        10  YY                  PIC X(2).                         01430000
001440        10  MM                  PIC X(2).                         01440000
001450        10  DD                  PIC X(2).                         01450000
001460        10  HH                  PIC X(2).                         01460000
001470        10  MI                  PIC X(2).                         01470000
001480        10  SS                  PIC X(2).                         01480000
001490        10  TT                  PIC X(2).                         01490000
001500        10  FILLER              PIC X(13).                        01500000
001510     05 TS-TIMESTAMP.                                             01510000
001520        10  CC                  PIC X(2).                         01520000
001530        10  YY                  PIC X(2).                         01530000
001540        10  TE-MARKER1          PIC X    VALUE '-'.               01540000
001550        10  MM                  PIC X(2).                         01550000
001560        10  TE-MARKER2          PIC X    VALUE '-'.               01560000
001570        10  DD                  PIC X(2).                         01570000
001580        10  TE-MARKER3          PIC X    VALUE '-'.               01580000
001590        10  HH                  PIC X(2).                         01590000
001600        10  TE-MARKER4          PIC X    VALUE '.'.               01600000
001610        10  MI                  PIC X(2).                         01610000
001620        10  TE-MARKER5          PIC X    VALUE '.'.               01620000
001630        10  SS                  PIC X(2).                         01630000
001640        10  TE-MARKER6          PIC X    VALUE '.'.               01640000
001650        10  TT                  PIC X(2).                         01650000
001660        10  NNNN                PIC 9(04) VALUE 0.                01660000
001670                                                                  01670000
001680                                                                  01680000
001690*DB2 GENERATED ROW COUNTERS                                       01690000
001700 01  WS-DB2-COUNTERS.                                             01700000
001710     10  WS-NB-EVEF-COUNT         PIC 9(7)    COMP-3 VALUE ZEROES.01710000
001720 LINKAGE SECTION.                                                 01720000
001730*----------------                                                 01730000
001740 01  LS-PARM-INPUT.                                               01740000
001750     02  LS-PARM                PIC S9(004) COMP.                 01750000
001760     02  LS-PARAM-IND           PIC X.                            01760000
001770     02  LS-DATE8               PIC  9(008).                      01770000
001780                                                                  01780000
001790                                                                  01790000
001800 PROCEDURE DIVISION USING LS-PARM-INPUT.                          01800000
001810 100-INITIALIZE.                                                  01810000
001820*DB2: Centralized initialization (all DCLGEN groups, constants, ti01820000
001830*DB2: Redundant INITIALIZE block removed (consolidated in 100-INIT01830000
001840     MOVE CS-PROGRAM   TO PROGRAM-NAME.                           01840000
001850     PERFORM 600-GET-TIMESTAMP.                                   01850000
001860     .                                                            01860000
001870                                                                  01870000
001880                                                                  01880000
001890*=======================================                          01890000
001900     PERFORM 600-GET-TIMESTAMP.                                   01900000
001910 MAIN.                                                            01910000
001920*-----                                                            01920000
001930     PERFORM INIT-TREATMENT                                       01930000
001940     PERFORM TREAT-MUTATIES UNTIL MUTATIES-EOF                    01940000
001950     PERFORM END-TREATMENT.                                       01950000
001960     DISPLAY 'TOTAL EVEF RECORDS   : ' WS-NB-EVEF-COUNT           01960000
001970                                                                  01970000
001980     STOP RUN                                                     01980000
001990 600-GET-TIMESTAMP.                                               01990000
002000     MOVE FUNCTION CURRENT-DATE            TO TS-SYSTEM.          02000000
002010     MOVE CC OF TS-SYSTEM             TO CC OF TS-TIMESTAMP       02010000
002020     MOVE YY OF TS-SYSTEM             TO YY OF TS-TIMESTAMP       02020000
002030     MOVE MM OF TS-SYSTEM             TO MM OF TS-TIMESTAMP       02030000
002040     MOVE DD OF TS-SYSTEM             TO DD OF TS-TIMESTAMP       02040000
002050     MOVE HH OF TS-SYSTEM             TO HH OF TS-TIMESTAMP       02050000
002060     MOVE MI OF TS-SYSTEM             TO MI OF TS-TIMESTAMP       02060000
002070     MOVE SS OF TS-SYSTEM             TO SS OF TS-TIMESTAMP       02070000
002080     MOVE TT OF TS-SYSTEM             TO TT OF TS-TIMESTAMP       02080000
002090     DISPLAY 'TIMESTAMP: ' TS-TIMESTAMP                           02090000
002100     .                                                            02100000
002110                                                                  02110000
002120     .                                                            02120000
002130                                                                  02130000
002140*----------------------------------------------------------------*02140000
002150 INIT-TREATMENT.                                                  02150000
002160*---------------                                                  02160000
002170     OPEN INPUT  FI-MUTATIES                                      02170000
002180     OUTPUT FO-MUTATIES                                           02180000
002190     SET MUTATIES-NOT-EOF TO TRUE.                                02190000
002200                                                                  02200000
002210* -- BINDS VOOR IDMS                                              02210000
002220     ON ANY-ERROR-STATUS                                          02220000
002230                                                                  02230000
002240     ON ANY-ERROR-STATUS                                          02240000
002250                                                                  02250000
002260     ON ANY-ERROR-STATUS                                          02260000
002270                                                                  02270000
002280* -- READY                                                        02280000
002290     ON ANY-ERROR-STATUS                                          02290000
002300                                                                  02300000
002310     PERFORM READ-MUTATIES                                        02310000
002320     .                                                            02320000
002330                                                                  02330000
002340*----------------------------------------------------------------*02340000
002350 END-TREATMENT.                                                   02350000
002360*--------------                                                   02360000
002370* -- FINISH                                                       02370000
002380*DB2: COMMIT removed; retrieval program is read-only.             02380000
002390     ON ANY-ERROR-STATUS                                          02390000
002400                                                                  02400000
002410     CLOSE FI-MUTATIES                                            02410000
002420     FO-MUTATIES                                                  02420000
002430                                                                  02430000
002440     DISPLAY '# TREATED  = ' COUNT-TREATED                        02440000
002450     .                                                            02450000
002460                                                                  02460000
002470*----------------------------------------------------------------*02470000
002480 TREAT-MUTATIES.                                                  02480000
002490*--------------                                                   02490000
002500     PERFORM SEARCH-MUTATIES.                                     02500000
002510     PERFORM MOVE-MUTATIES.                                       02510000
002520     PERFORM WRITE-MUTATIES.                                      02520000
002530     PERFORM READ-MUTATIES                                        02530000
002540     .                                                            02540000
002550                                                                  02550000
002560*----------------------------------------------------------------*02560000
002570 SEARCH-MUTATIES.                                                 02570000
002580*---------------                                                  02580000
002590     MOVE SPACES              TO KY-EFFECT      OF VMBEFF.        02590000
002600     MOVE '1002' TO CT-RKTPROD-479BEFF OF DCLDZBEFFTV.            02600000
002610     MOVE WS-IN-NR-TIT-BC     TO NR-ID-STOCK-CD OF VMBEFF.        02610000
002620     MOVE WS-NR-SUITE         TO NS-DBSTK-479BEFF OF DCLDZBEFFTV. 02620000
002630                                                                  02630000
002640*DB2: Expanded LRF FIRST VMBTL07-R01 WHERE ALL-VMBEVEF-BY-VMBEFF  02640000
002650*  -> VMBEVEF WITHIN VMBEFF-VMBEVEF.                              02650000
002660*DB2: Converted OBTAIN FIRST VMBEVEF WITHIN VMBEFF-VMBEVEF.       02660000
002670     PERFORM 710-OPEN-DZEVEFC1.                                   02670000
002680     PERFORM 720-FETCH-DZEVEFC1 UNTIL DZEVEFC1-EOC.               02680000
002690     PERFORM 730-CLOSE-DZEVEFC1.                                  02690000
002700                                                                  02700000
002710     IF SQLCODE = 100                                             02710000
002720        DISPLAY 'VMBEFF NOT FOUND : ' KY-EFFECT OF VMBEFF         02720000
002730        CALL USERABEN                                             02730000
002740     END-IF.                                                      02740000
002750     IF SQLCODE = 100                                             02750000
002760        DISPLAY 'VMBEVEF NOT FOUND : ' KY-EFFECT OF VMBEFF        02760000
002770        CALL USERABEN                                             02770000
002780     END-IF.                                                      02780000
002790                                                                  02790000
002800* -- ZOEK DE MUTATIE                                              02800000
002810     PERFORM UNTIL SQLCODE = 100                                  02810000
002820        OR CT-EVENT OF VMBEVEF = '0092'.                          02820000
002830*DB2: Expanded LRF NEXT VMBTL07-R01 WHERE ALL-VMBEVEF-BY-VMBEFF ->02830000
002840*  VMBEVEF WITHIN VMBEFF-VMBEVEF.                                 02840000
002850*DB2: Converted OBTAIN NEXT VMBEVEF WITHIN VMBEFF-VMBEVEF.        02850000
002860     END-PERFORM.                                                 02860000
002870                                                                  02870000
002880     IF SQLCODE = 100                                             02880000
002890        DISPLAY 'NO MORE VMBEVEF : ' KY-EFFECT OF VMBEFF          02890000
002900        CALL USERABEN                                             02900000
002910     END-IF.                                                      02910000
002920                                                                  02920000
002930*----------------------------------------------------------------*02930000
002940 MOVE-MUTATIES.                                                   02940000
002950*-------------                                                    02950000
002960     INITIALIZE VMDZ510I                                          02960000
002970     REPLACING ALPHANUMERIC BY SPACES                             02970000
002980     NUMERIC BY ZEROES.                                           02980000
002990                                                                  02990000
003000     MOVE NR-IDGOOD-479EVEF OF DCLDZEVEFTV TO WS-NR-ID-GOOD.      03000000
003010                                                                  03010000
003020     MOVE NR-CI               OF VMBEVEF                          03020000
003030     TO NR-CIO-FORM-AS      OF VMDZ510I.                          03030000
003040     MOVE WS-DA-CREA                                              03040000
003050     TO DA-CREA-FORM-AS-R   OF VMDZ510I.                          03050000
003060     STRING DA-CR-FORM-AS-Y   OF VMDZ510I '-'                     03060000
003070        DA-CR-FORM-AS-M   OF VMDZ510I '-'                         03070000
003080        DA-CR-FORM-AS-D   OF VMDZ510I '-'                         03080000
003090        '01.01.01.000001'                                         03090000
003100        DELIMITED BY SIZE                                         03100000
003110        INTO TS-CREA-OORD      OF VMDZ510I.                       03110000
003120        MOVE WS-NR-ID                                             03120000
003130        TO NR-ID-FORM-AS       OF VMDZ510I.                       03130000
003140        MOVE WS-CT-OPG                                            03140000
003150        TO CT-OPG-FORM-AS-R    OF VMDZ510I.                       03150000
003160        MOVE WS-CT-OPD                                            03160000
003170        TO CT-OPD-FORM-AS-R    OF VMDZ510I.                       03170000
003180                                                                  03180000
003190        MOVE NR-IDISSUE-479BEFF OF DCLDZBEFFTV TO WS-NR-ID-ISSUE  03190000
003200        MOVE NR-CDISSUE-479BEFF OF DCLDZBEFFTV TO WS-NR-CD-ISSUE  03200000
003210        MOVE WS-NR-ISSUE  TO NR-ISSUIN-OORD    OF VMDZ510I.       03210000
003220        MOVE AM-CNSTK-479BEFF OF DCLDZBEFFTV                      03220000
003230        TO AM-CNS-FORM-AS      OF VMDZ510I.                       03230000
003240        MOVE NR-ID-STOCK-CD      OF VMBEFF                        03240000
003250        TO NR-ST-FORM-AS-R     OF VMDZ510I.                       03250000
003260        MOVE NR-ID-STOCK-CD      OF VMBEFF                        03260000
003270        TO NR-STIN-OORD        OF VMDZ510I.                       03270000
003280        MOVE NS-DBSTK-479BEFF OF DCLDZBEFFTV                      03280000
003290        TO NS-DBST-OORD        OF VMDZ510I.                       03290000
003300        IF NX-CPCRESK-479BEFF OF DCLDZBEFFTV = 0                  03300000
003310           MOVE AM-CNDSTK-479BEFF OF DCLDZBEFFTV                  03310000
003320           TO AM-CND-FORM-AS      OF VMDZ510I                     03320000
003330        ELSE                                                      03330000
003340           MOVE AM-INTERSK-479BEFF OF DCLDZBEFFTV                 03340000
003350           TO AM-INTER-FORM-AS    OF VMDZ510I                     03350000
003360        END-IF.                                                   03360000
003370        MOVE CO-IDPRKSK-479BEFF OF DCLDZBEFFTV                    03370000
003380        TO NR-ID-040SECU       OF VMDZ510I.                       03380000
003390        MOVE NS-IRMOSTK-479BEFF OF DCLDZBEFFTV                    03390000
003400        TO NS-SEQ-040IRMO      OF VMDZ510I.                       03400000
003410        MOVE DA-UBSECIS-479BEFF OF DCLDZBEFFTV                    03410000
003420        TO DA-UB-FORM-AS       OF VMDZ510I.                       03420000
003430        MOVE DA-CREVTPD-479EVEF OF DCLDZEVEFTV                    03430000
003440        TO DA-COMPTABILISATION-OPER OF VMDZ510I.                  03440000
003450        MOVE DA-CREVTPD-479EVEF OF DCLDZEVEFTV                    03450000
003460        TO DA-EXEC-OORD        OF VMDZ510I.                       03460000
003470                                                                  03470000
003480        MOVE NX-CPCRESK-479BEFF OF DCLDZBEFFTV                    03480000
003490        TO NS-RANK-COUP        OF VMDZ510I.                       03490000
003500        MOVE NX-CPAIDSK-479BEFF OF DCLDZBEFFTV                    03500000
003510        TO NX-CPAID-STOCK      OF VMDZ510I.                       03510000
003520*    MOVE NX-CPFDU-STOCK      OF VMBEFF                           03520000
003530                                                                  03530000
003540* EXTRA ZONES OPVULLEN                                            03540000
003550                                                                  03550000
003560        EVALUATE WS-CT-OPD                                        03560000
003570          WHEN 00                                                 03570000
003580               MOVE 'MU' TO CO-TYPOPER-OORD OF VMDZ510I           03580000
003590          WHEN OTHER                                              03590000
003600               MOVE '??' TO CO-TYPOPER-OORD OF VMDZ510I           03600000
003610               DISPLAY 'ABEND VERKEERDE CT-OPD = '                03610000
003620               WS-CT-OPD                                          03620000
003630               DISPLAY  VMBEFF                                    03630000
003640               DISPLAY  VMBEVEF                                   03640000
003650               CALL USERABEN                                      03650000
003660        END-EVALUATE.                                             03660000
003670* UITGIFTE = SRW DUS '1'                                          03670000
003680        MOVE '1' TO CO-ISSUIN-OORD OF VMDZ510I.                   03680000
003690        MOVE 001 TO NB-ST-OORD     OF VMDZ510I.                   03690000
003700* EFFECT = IKB = DEXIA DUS '1'                                    03700000
003710        MOVE '1' TO CO-STIN-OORD   OF VMDZ510I.                   03710000
003720                                                                  03720000
003730        ADD 1 TO VOLGNUMMER.                                      03730000
003740        STRING 'CIR '                                             03740000
003750           CT-OPD-FORM-AS OF VMDZ510I ' '                         03750000
003760           VOLGNUMMER                                             03760000
003770           DELIMITED BY SIZE                                      03770000
003780           INTO NR-REFORD-OORD OF VMDZ510I.                       03780000
003790                                                                  03790000
003800* EXTRA'S ANNIE STEPPE                                            03800000
003810           STRING 'X'                                             03810000
003820              '000000'                                            03820000
003830              '      '                                            03830000
003840              DELIMITED BY SIZE                                   03840000
003850              INTO NR-TRANS-OORD  OF VMDZ510I.                    03850000
003860* 10=AGENCY 11=ZETEL                                              03860000
003870*    IF NR-CIO-FORM-AS OF VMBD510I =                              03870000
003880*       NR-CIW-FORM-AS OF VMBD510I                                03880000
003890              MOVE '10' TO CO-TYPKAN2-OORD OF VMDZ510I            03890000
003900*    ELSE                                                         03900000
003910*      MOVE '11' TO CO-TYPKAN2-OORD OF VMBD510I                   03910000
003920*    END-IF.                                                      03920000
003930              MOVE 'DX' TO CO-BANK-OORD    OF VMDZ510I.           03930000
003940                                                                  03940000
003950              MOVE WS-OLD-CI TO NR-CIINPTR-OORD OF VMDZ510I.      03950000
003960                                                                  03960000
003970*----------------------------------------------------------------*03970000
003980 WRITE-MUTATIES.                                                  03980000
003990*--------------                                                   03990000
004000     ADD 1 TO COUNT-TREATED                                       04000000
004010     WRITE FO-MUTATIES-REC FROM VMDZ510I                          04010000
004020     .                                                            04020000
004030                                                                  04030000
004040*----------------------------------------------------------------*04040000
004050 READ-MUTATIES.                                                   04050000
004060*-------------                                                    04060000
004070     READ FI-MUTATIES INTO    WS-MUTATIES                         04070000
004080        AT END                                                    04080000
004090        SET MUTATIES-EOF TO TRUE                                  04090000
004100        NOT AT END                                                04100000
004110        CONTINUE                                                  04110000
004120     END-READ                                                     04120000
004130     .                                                            04130000
004140                                                                  04140000
004150/---------------------------------------------------------------* 04150000
004160*    ERROR HANDLING                                               04160000
004170*---------------------------------------------------------------* 04170000
004180                                                                  04180000
004190*DB2 GENERATED CURSOR OPEN FETCH CLOSE PARAGRAPHS              *  04190000
004200                                                                  04200000
004210 710-OPEN-DZEVEFC1.                                               04210000
004220D    DISPLAY '710-OPEN-DZEVEFC1.'                                 04220000
004230     MOVE 710    TO SQL-LOCATION                                  04230000
004240                                                                  04240000
004250     EXEC SQL                                                     04250000
004260       OPEN DZEVEFC1                                              04260000
004270     END-EXEC                                                     04270000
004280                                                                  04280000
004290     EVALUATE SQLCODE                                             04290000
004300       WHEN ZERO                                                  04300000
004310            SET DZEVEFC1-NOT-EOC TO TRUE                          04310000
004320       WHEN OTHER                                                 04320000
004330            MOVE 710    TO SQL-LOCATION                           04330000
004340            DISPLAY 'ERROR WHILE OPENING CURSOR DZEVEFC1'         04340000
004350            PERFORM SQLERROR                                      04350000
004360     END-EVALUATE                                                 04360000
004370     .                                                            04370000
004380                                                                  04380000
004390 720-FETCH-DZEVEFC1.                                              04390000
004400D    DISPLAY '720-FETCH-DZEVEFC1.'                                04400000
004410     SET DZEVEFC1-NOT-EOC TO TRUE                                 04410000
004420     MOVE 720    TO SQL-LOCATION                                  04420000
004430                                                                  04430000
004440     EXEC SQL                                                     04440000
004450       FETCH DZEVEFC1                                             04450000
004460       INTO :DCLDZEVEFTV.DA-CREVTPD-479EVEF                       04460000
004470       , :DCLDZEVEFTV.NR-IDGOOD-479EVEF                           04470000
004480       , :DCLDZEVEFTV.NR-ID-479EVEF                               04480000
004490     END-EXEC                                                     04490000
004500                                                                  04500000
004510     EVALUATE SQLCODE                                             04510000
004520       WHEN ZERO                                                  04520000
004530            ADD 1 TO WS-NB-EVEF-COUNT                             04530000
004540            CONTINUE                                              04540000
004550       WHEN 100                                                   04550000
004560            SET DZEVEFC1-EOC TO TRUE                              04560000
004570       WHEN OTHER                                                 04570000
004580            MOVE 720    TO SQL-LOCATION                           04580000
004590            DISPLAY 'ERROR WHILE FETCHING CURSOR DZEVEFC1'        04590000
004600            DISPLAY 'DA-CREVTPD-479EVEF : ' DA-CREVTPD-479EVEF    04600000
004610            OF DCLDZEVEFTV                                        04610000
004620            DISPLAY 'NR-IDGOOD-479EVEF  : ' NR-IDGOOD-479EVEF     04620000
004630            OF DCLDZEVEFTV                                        04630000
004640            DISPLAY 'NR-ID-479EVEF      : ' NR-ID-479EVEF         04640000
004650            OF DCLDZEVEFTV                                        04650000
004660            PERFORM SQLERROR                                      04660000
004670     END-EVALUATE                                                 04670000
004680     .                                                            04680000
004690                                                                  04690000
004700 730-CLOSE-DZEVEFC1.                                              04700000
004710D    DISPLAY '730-CLOSE-DZEVEFC1.'                                04710000
004720     MOVE 730    TO SQL-LOCATION                                  04720000
004730                                                                  04730000
004740     EXEC SQL                                                     04740000
004750       CLOSE DZEVEFC1                                             04750000
004760     END-EXEC                                                     04760000
004770                                                                  04770000
004780     EVALUATE SQLCODE                                             04780000
004790       WHEN ZERO                                                  04790000
004800            CONTINUE                                              04800000
004810       WHEN OTHER                                                 04810000
004820            MOVE 730    TO SQL-LOCATION                           04820000
004830            DISPLAY 'ERROR WHILE CLOSING CURSOR DZEVEFC1'         04830000
004840            PERFORM SQLERROR                                      04840000
004850     END-EVALUATE                                                 04850000
004860     .                                                            04860000
004870                                                                  04870000
004880*SQLERROR ROUTINE.                                                04880000
004890     EXEC SQL                                                     04890000
004900       INCLUDE SQLERROR                                           04900000
004910     END-EXEC.                                                    04910000
