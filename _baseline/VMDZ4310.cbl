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
001190     EXEC SQL DECLARE DZEVEFC1 CURSOR WITH HOLD FOR               01190000
001200       SELECT DA_CREVTPD_479EVEF                                  01200000
001210            , NR_IDGOOD_479EVEF                                   01210000
001220            , NR_ID_479EVEF                                       01220000
001230       FROM DZEVEFTV                                              01230000
001240       ORDER BY NR_ID_479EVEF DESC                                01240000
001250       FOR READ ONLY                                              01250000
001260       QUERYNO 254                                                01260000
001270     END-EXEC.                                                    01270000
001280                                                                  01280000
001290                                                                  01290000
001300*DB2 GENERATED WORKING STORAGE                                    01300000
001310 01  WS-DB2-GENERATED.                                            01310000
001320     10  CS-PROGRAM               PIC X(8)    VALUE 'VMDZ4310'.   01320000
001330     10  WS-NB-EVEF-COUNT         PIC 9(7)    COMP-3 VALUE ZEROES.01330000
001340                                                                  01340000
001350*DB2 GENERATED TIMESTAMP AND AUDIT WORKING STORAGE                01350000
001360 01  WS-TIMESTAMP-FIELDS.                                         01360000
001370     05 TS-SYSTEM.                                                01370000
001380        10  DA-SYS.                                               01380000
001390            15  DA-SYS-CCYY.                                      01390000
001400                20  CC            PIC X(2).                       01400000
001410                20  YY            PIC X(2).                       01410000
001420            15  MM                PIC X(2).                       01420000
001430            15  DD                PIC X(2).                       01430000
001440        10  HR-SYS.                                               01440000
001450            15  HH                PIC X(2).                       01450000
001460            15  MI                PIC X(2).                       01460000
001470            15  SS                PIC X(2).                       01470000
001480            15  TT                PIC X(2).                       01480000
001490     05 TS-TIMESTAMP.                                             01490000
001500        10  CC                    PIC X(2).                       01500000
001510        10  YY                    PIC X(2).                       01510000
001520        10  TE-MARKER1            PIC X             VALUE '-'.    01520000
001530        10  MM                    PIC X(2).                       01530000
001540        10  TE-MARKER2            PIC X             VALUE '-'.    01540000
001550        10  DD                    PIC X(2).                       01550000
001560        10  TE-MARKER3            PIC X             VALUE '-'.    01560000
001570        10  HH                    PIC X(2).                       01570000
001580        10  TE-MARKER4            PIC X             VALUE '.'.    01580000
001590        10  MI                    PIC X(2).                       01590000
001600        10  TE-MARKER5            PIC X             VALUE '.'.    01600000
001610        10  SS                    PIC X(2).                       01610000
001620        10  TE-MARKER6            PIC X             VALUE '.'.    01620000
001630        10  TT                    PIC X(2).                       01630000
001640        10  NNNN                  PIC 9(04)         VALUE 0.      01640000
001650                                                                  01650000
001660 LINKAGE SECTION.                                                 01660000
001670*----------------                                                 01670000
001680 01  LS-PARM-INPUT.                                               01680000
001690     02  LS-PARM                PIC S9(004) COMP.                 01690000
001700     02  LS-PARAM-IND           PIC X.                            01700000
001710     02  LS-DATE8               PIC  9(008).                      01710000
001720                                                                  01720000
001730                                                                  01730000
001740 PROCEDURE DIVISION USING LS-PARM-INPUT.                          01740000
001750*=======================================                          01750000
001760     PERFORM 600-GET-TIMESTAMP.                                   01760000
001770                                                                  01770000
001780 MAIN.                                                            01780000
001790*-----                                                            01790000
001800     PERFORM INIT-TREATMENT                                       01800000
001810     PERFORM TREAT-MUTATIES UNTIL MUTATIES-EOF                    01810000
001820     PERFORM END-TREATMENT                                        01820000
001830     DISPLAY 'TOTAL EVEF RECORDS   : ' WS-NB-EVEF-COUNT           01830000
001840                                                                  01840000
001850     STOP RUN                                                     01850000
001860     .                                                            01860000
001870                                                                  01870000
001880*----------------------------------------------------------------*01880000
001890 INIT-TREATMENT.                                                  01890000
001900*---------------                                                  01900000
001910     OPEN INPUT  FI-MUTATIES                                      01910000
001920     OUTPUT FO-MUTATIES                                           01920000
001930     SET MUTATIES-NOT-EOF TO TRUE.                                01930000
001940                                                                  01940000
001950* -- BINDS VOOR IDMS                                              01950000
001960     ON ANY-ERROR-STATUS                                          01960000
001970                                                                  01970000
001980     ON ANY-ERROR-STATUS                                          01980000
001990                                                                  01990000
002000     ON ANY-ERROR-STATUS                                          02000000
002010                                                                  02010000
002020* -- READY                                                        02020000
002030     ON ANY-ERROR-STATUS                                          02030000
002040                                                                  02040000
002050     PERFORM READ-MUTATIES                                        02050000
002060     .                                                            02060000
002070                                                                  02070000
002080*----------------------------------------------------------------*02080000
002090 END-TREATMENT.                                                   02090000
002100*--------------                                                   02100000
002110* -- FINISH                                                       02110000
002120     ON ANY-ERROR-STATUS                                          02120000
002130                                                                  02130000
002140     CLOSE FI-MUTATIES                                            02140000
002150     FO-MUTATIES                                                  02150000
002160                                                                  02160000
002170     DISPLAY '# TREATED  = ' COUNT-TREATED                        02170000
002180     .                                                            02180000
002190                                                                  02190000
002200*----------------------------------------------------------------*02200000
002210 TREAT-MUTATIES.                                                  02210000
002220*--------------                                                   02220000
002230     PERFORM SEARCH-MUTATIES.                                     02230000
002240     PERFORM MOVE-MUTATIES.                                       02240000
002250     PERFORM WRITE-MUTATIES.                                      02250000
002260     PERFORM READ-MUTATIES                                        02260000
002270     .                                                            02270000
002280                                                                  02280000
002290*----------------------------------------------------------------*02290000
002300 SEARCH-MUTATIES.                                                 02300000
002310*---------------                                                  02310000
002320     MOVE SPACES              TO KY-EFFECT      OF VMBEFF.        02320000
002330     MOVE '1002' TO CT-RKTPROD-479BEFF OF DCLDZBEFFTV.            02330000
002340     MOVE WS-IN-NR-TIT-BC     TO NR-ID-STOCK-CD OF VMBEFF.        02340000
002350     MOVE WS-NR-SUITE         TO NS-DBSTK-479BEFF OF DCLDZBEFFTV. 02350000
002360                                                                  02360000
002370*DB2: Expanded LRF FIRST VMBTL07-R01 WHERE ALL-VMBEVEF-BY-VMBEFF  02370000
002380*  -> VMBEVEF WITHIN VMBEFF-VMBEVEF.                              02380000
002390     INITIALIZE DCLDZEVEFTV                                       02390000
002400     PERFORM 710-OPEN-DZEVEFC1.                                   02400000
002410     PERFORM 720-FETCH-DZEVEFC1 UNTIL DZEVEFC1-EOC.               02410000
002420     PERFORM 730-CLOSE-DZEVEFC1.                                  02420000
002430                                                                  02430000
002440     IF SQLCODE = 100                                             02440000
002450        DISPLAY 'VMBEFF NOT FOUND : ' KY-EFFECT OF VMBEFF         02450000
002460        CALL USERABEN                                             02460000
002470     END-IF.                                                      02470000
002480     IF SQLCODE = 100                                             02480000
002490        DISPLAY 'VMBEVEF NOT FOUND : ' KY-EFFECT OF VMBEFF        02490000
002500        CALL USERABEN                                             02500000
002510     END-IF.                                                      02510000
002520                                                                  02520000
002530* -- ZOEK DE MUTATIE                                              02530000
002540     PERFORM UNTIL SQLCODE = 100                                  02540000
002550                OR CT-EVENT OF VMBEVEF = '0092'.                  02550000
002560*DB2: Expanded LRF NEXT VMBTL07-R01 WHERE ALL-VMBEVEF-BY-VMBEFF ->02560000
002570*  VMBEVEF WITHIN VMBEFF-VMBEVEF.                                 02570000
002580     END-PERFORM.                                                 02580000
002590                                                                  02590000
002600     IF SQLCODE = 100                                             02600000
002610        DISPLAY 'NO MORE VMBEVEF : ' KY-EFFECT OF VMBEFF          02610000
002620        CALL USERABEN                                             02620000
002630     END-IF.                                                      02630000
002640                                                                  02640000
002650*----------------------------------------------------------------*02650000
002660 MOVE-MUTATIES.                                                   02660000
002670*-------------                                                    02670000
002680     INITIALIZE VMDZ510I                                          02680000
002690     REPLACING ALPHANUMERIC BY SPACES                             02690000
002700     NUMERIC BY ZEROES.                                           02700000
002710                                                                  02710000
002720     MOVE NR-IDGOOD-479EVEF OF DCLDZEVEFTV TO WS-NR-ID-GOOD.      02720000
002730                                                                  02730000
002740     MOVE NR-CI               OF VMBEVEF                          02740000
002750       TO NR-CIO-FORM-AS      OF VMDZ510I.                        02750000
002760     MOVE WS-DA-CREA                                              02760000
002770       TO DA-CREA-FORM-AS-R   OF VMDZ510I.                        02770000
002780     STRING DA-CR-FORM-AS-Y   OF VMDZ510I '-'                     02780000
002790        DA-CR-FORM-AS-M   OF VMDZ510I '-'                         02790000
002800        DA-CR-FORM-AS-D   OF VMDZ510I '-'                         02800000
002810            '01.01.01.000001'                                     02810000
002820        DELIMITED BY SIZE                                         02820000
002830       INTO TS-CREA-OORD      OF VMDZ510I.                        02830000
002840        MOVE WS-NR-ID                                             02840000
002850       TO NR-ID-FORM-AS       OF VMDZ510I.                        02850000
002860        MOVE WS-CT-OPG                                            02860000
002870       TO CT-OPG-FORM-AS-R    OF VMDZ510I.                        02870000
002880        MOVE WS-CT-OPD                                            02880000
002890       TO CT-OPD-FORM-AS-R    OF VMDZ510I.                        02890000
002900                                                                  02900000
002910        MOVE NR-IDISSUE-479BEFF OF DCLDZBEFFTV TO WS-NR-ID-ISSUE  02910000
002920        MOVE NR-CDISSUE-479BEFF OF DCLDZBEFFTV TO WS-NR-CD-ISSUE  02920000
002930        MOVE WS-NR-ISSUE  TO NR-ISSUIN-OORD    OF VMDZ510I.       02930000
002940        MOVE AM-CNSTK-479BEFF OF DCLDZBEFFTV                      02940000
002950       TO AM-CNS-FORM-AS      OF VMDZ510I.                        02950000
002960        MOVE NR-ID-STOCK-CD      OF VMBEFF                        02960000
002970       TO NR-ST-FORM-AS-R     OF VMDZ510I.                        02970000
002980        MOVE NR-ID-STOCK-CD      OF VMBEFF                        02980000
002990       TO NR-STIN-OORD        OF VMDZ510I.                        02990000
003000        MOVE NS-DBSTK-479BEFF OF DCLDZBEFFTV                      03000000
003010       TO NS-DBST-OORD        OF VMDZ510I.                        03010000
003020        IF NX-CPCRESK-479BEFF OF DCLDZBEFFTV = 0                  03020000
003030           MOVE AM-CNDSTK-479BEFF OF DCLDZBEFFTV                  03030000
003040         TO AM-CND-FORM-AS      OF VMDZ510I                       03040000
003050        ELSE                                                      03050000
003060           MOVE AM-INTERSK-479BEFF OF DCLDZBEFFTV                 03060000
003070         TO AM-INTER-FORM-AS    OF VMDZ510I                       03070000
003080        END-IF.                                                   03080000
003090        MOVE CO-IDPRKSK-479BEFF OF DCLDZBEFFTV                    03090000
003100       TO NR-ID-040SECU       OF VMDZ510I.                        03100000
003110        MOVE NS-IRMOSTK-479BEFF OF DCLDZBEFFTV                    03110000
003120       TO NS-SEQ-040IRMO      OF VMDZ510I.                        03120000
003130        MOVE DA-UBSECIS-479BEFF OF DCLDZBEFFTV                    03130000
003140       TO DA-UB-FORM-AS       OF VMDZ510I.                        03140000
003150        MOVE DA-CREVTPD-479EVEF OF DCLDZEVEFTV                    03150000
003160       TO DA-COMPTABILISATION-OPER OF VMDZ510I.                   03160000
003170        MOVE DA-CREVTPD-479EVEF OF DCLDZEVEFTV                    03170000
003180       TO DA-EXEC-OORD        OF VMDZ510I.                        03180000
003190                                                                  03190000
003200        MOVE NX-CPCRESK-479BEFF OF DCLDZBEFFTV                    03200000
003210       TO NS-RANK-COUP        OF VMDZ510I.                        03210000
003220        MOVE NX-CPAIDSK-479BEFF OF DCLDZBEFFTV                    03220000
003230       TO NX-CPAID-STOCK      OF VMDZ510I.                        03230000
003240*    MOVE NX-CPFDU-STOCK      OF VMBEFF                           03240000
003250                                                                  03250000
003260* EXTRA ZONES OPVULLEN                                            03260000
003270                                                                  03270000
003280        EVALUATE WS-CT-OPD                                        03280000
003290          WHEN 00                                                 03290000
003300               MOVE 'MU' TO CO-TYPOPER-OORD OF VMDZ510I           03300000
003310          WHEN OTHER                                              03310000
003320               MOVE '??' TO CO-TYPOPER-OORD OF VMDZ510I           03320000
003330               DISPLAY 'ABEND VERKEERDE CT-OPD = '                03330000
003340               WS-CT-OPD                                          03340000
003350               DISPLAY  VMBEFF                                    03350000
003360               DISPLAY  VMBEVEF                                   03360000
003370               CALL USERABEN                                      03370000
003380        END-EVALUATE.                                             03380000
003390* UITGIFTE = SRW DUS '1'                                          03390000
003400        MOVE '1' TO CO-ISSUIN-OORD OF VMDZ510I.                   03400000
003410        MOVE 001 TO NB-ST-OORD     OF VMDZ510I.                   03410000
003420* EFFECT = IKB = DEXIA DUS '1'                                    03420000
003430        MOVE '1' TO CO-STIN-OORD   OF VMDZ510I.                   03430000
003440                                                                  03440000
003450        ADD 1 TO VOLGNUMMER.                                      03450000
003460        STRING 'CIR '                                             03460000
003470           CT-OPD-FORM-AS OF VMDZ510I ' '                         03470000
003480           VOLGNUMMER                                             03480000
003490           DELIMITED BY SIZE                                      03490000
003500       INTO NR-REFORD-OORD OF VMDZ510I.                           03500000
003510                                                                  03510000
003520* EXTRA'S ANNIE STEPPE                                            03520000
003530           STRING 'X'                                             03530000
003540            '000000'                                              03540000
003550            '      '                                              03550000
003560              DELIMITED BY SIZE                                   03560000
003570       INTO NR-TRANS-OORD  OF VMDZ510I.                           03570000
003580* 10=AGENCY 11=ZETEL                                              03580000
003590*    IF NR-CIO-FORM-AS OF VMBD510I =                              03590000
003600*       NR-CIW-FORM-AS OF VMBD510I                                03600000
003610              MOVE '10' TO CO-TYPKAN2-OORD OF VMDZ510I            03610000
003620*    ELSE                                                         03620000
003630*      MOVE '11' TO CO-TYPKAN2-OORD OF VMBD510I                   03630000
003640*    END-IF.                                                      03640000
003650              MOVE 'DX' TO CO-BANK-OORD    OF VMDZ510I.           03650000
003660                                                                  03660000
003670              MOVE WS-OLD-CI TO NR-CIINPTR-OORD OF VMDZ510I.      03670000
003680                                                                  03680000
003690*----------------------------------------------------------------*03690000
003700 WRITE-MUTATIES.                                                  03700000
003710*--------------                                                   03710000
003720     ADD 1 TO COUNT-TREATED                                       03720000
003730     WRITE FO-MUTATIES-REC FROM VMDZ510I                          03730000
003740     .                                                            03740000
003750                                                                  03750000
003760*----------------------------------------------------------------*03760000
003770 READ-MUTATIES.                                                   03770000
003780*-------------                                                    03780000
003790     READ FI-MUTATIES INTO    WS-MUTATIES                         03790000
003800        AT END                                                    03800000
003810        SET MUTATIES-EOF TO TRUE                                  03810000
003820     NOT AT END                                                   03820000
003830        CONTINUE                                                  03830000
003840     END-READ                                                     03840000
003850     .                                                            03850000
003860                                                                  03860000
003870/---------------------------------------------------------------* 03870000
003880*    ERROR HANDLING                                               03880000
003890*---------------------------------------------------------------* 03890000
003900                                                                  03900000
003910*DB2 GENERATED CURSOR OPEN FETCH CLOSE PARAGRAPHS              *  03910000
003920                                                                  03920000
003930 710-OPEN-DZEVEFC1.                                               03930000
003940D    DISPLAY '710-OPEN-DZEVEFC1.'                                 03940000
003950     MOVE 710    TO SQL-LOCATION                                  03950000
003960                                                                  03960000
003970     EXEC SQL                                                     03970000
003980       OPEN DZEVEFC1                                              03980000
003990     END-EXEC                                                     03990000
004000                                                                  04000000
004010     EVALUATE SQLCODE                                             04010000
004020       WHEN ZERO                                                  04020000
004030            SET DZEVEFC1-NOT-EOC TO TRUE                          04030000
004040       WHEN OTHER                                                 04040000
004050            DISPLAY 'ERROR WHILE OPENING CURSOR DZEVEFC1'         04050000
004060            PERFORM SQLERROR                                      04060000
004070     END-EVALUATE                                                 04070000
004080     .                                                            04080000
004090                                                                  04090000
004100 720-FETCH-DZEVEFC1.                                              04100000
004110D    DISPLAY '720-FETCH-DZEVEFC1.'                                04110000
004120     SET DZEVEFC1-NOT-EOC TO TRUE                                 04120000
004130     MOVE 720    TO SQL-LOCATION                                  04130000
004140                                                                  04140000
004150     EXEC SQL                                                     04150000
004160       FETCH DZEVEFC1                                             04160000
004170        INTO :DCLDZEVEFTV.DA-CREVTPD-479EVEF                      04170000
004180           , :DCLDZEVEFTV.NR-IDGOOD-479EVEF                       04180000
004190           , :DCLDZEVEFTV.NR-ID-479EVEF                           04190000
004200     END-EXEC                                                     04200000
004210                                                                  04210000
004220     EVALUATE SQLCODE                                             04220000
004230       WHEN ZERO                                                  04230000
004240            ADD 1 TO WS-NB-EVEF-COUNT                             04240000
004250            PERFORM MOVE-MUTATIES                                 04250000
004260       WHEN 100                                                   04260000
004270            SET DZEVEFC1-EOC TO TRUE                              04270000
004280       WHEN OTHER                                                 04280000
004290            DISPLAY 'ERROR WHILE FETCHING CURSOR DZEVEFC1'        04290000
004300            PERFORM SQLERROR                                      04300000
004310     END-EVALUATE                                                 04310000
004320     .                                                            04320000
004330                                                                  04330000
004340 730-CLOSE-DZEVEFC1.                                              04340000
004350D    DISPLAY '730-CLOSE-DZEVEFC1.'                                04350000
004360     MOVE 730    TO SQL-LOCATION                                  04360000
004370                                                                  04370000
004380     EXEC SQL                                                     04380000
004390       CLOSE DZEVEFC1                                             04390000
004400     END-EXEC                                                     04400000
004410                                                                  04410000
004420     EVALUATE SQLCODE                                             04420000
004430       WHEN ZERO                                                  04430000
004440            CONTINUE                                              04440000
004450       WHEN OTHER                                                 04450000
004460            DISPLAY 'ERROR WHILE CLOSING CURSOR DZEVEFC1'         04460000
004470            PERFORM SQLERROR                                      04470000
004480     END-EVALUATE                                                 04480000
004490     .                                                            04490000
004500                                                                  04500000
004510                                                                  04510000
004520 600-GET-TIMESTAMP.                                               04520000
004530D    DISPLAY '600-GET-TIMESTAMP.'                                 04530000
004540     MOVE FUNCTION CURRENT-DATE            TO TS-SYSTEM.          04540000
004550     MOVE CC OF TS-SYSTEM             TO CC OF TS-TIMESTAMP       04550000
004560     MOVE YY OF TS-SYSTEM             TO YY OF TS-TIMESTAMP       04560000
004570     MOVE MM OF TS-SYSTEM             TO MM OF TS-TIMESTAMP       04570000
004580     MOVE DD OF TS-SYSTEM             TO DD OF TS-TIMESTAMP       04580000
004590     MOVE HH OF TS-SYSTEM             TO HH OF TS-TIMESTAMP       04590000
004600     MOVE MI OF TS-SYSTEM             TO MI OF TS-TIMESTAMP       04600000
004610     MOVE SS OF TS-SYSTEM             TO SS OF TS-TIMESTAMP       04610000
004620     MOVE TT OF TS-SYSTEM             TO TT OF TS-TIMESTAMP       04620000
004630     DISPLAY 'TIMESTAMP: ' TS-TIMESTAMP                           04630000
004640     .                                                            04640000
004650                                                                  04650000
004660*SQLERROR ROUTINE.                                                04660000
004670     EXEC SQL                                                     04670000
004680          INCLUDE SQLERROR                                        04680000
004690     END-EXEC.                                                    04690000
