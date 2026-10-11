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
000250 DATE-WRITTEN. 2026-10-12.                                        00250000
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
001410     EXEC SQL DECLARE DZBEFFC1 CURSOR WITH HOLD FOR               01410000
001420       SELECT CT_RKTPROD_479BEFF                                  01420000
001430            , NR_IDSTOCK_479BEFF                                  01430000
001440            , NR_CDSTK_479BEFF                                    01440000
001450            , NS_DBSTK_479BEFF                                    01450000
001460       FROM DZBEFFTV                                              01460000
001470       WHERE CO_IDISSUS_479WCEF = :DCLDZWCEFTV.CO-IDISSUS-479WCEF 01470000
001480         AND NS_IRMOS_479WCEF = :DCLDZWCEFTV.NS-IRMOS-479WCEF     01480000
001490         AND DA_UBSECIS_479WCEF = :DCLDZWCEFTV.DA-UBSECIS-479WCEF 01490000
001500       FOR READ ONLY                                              01500000
001510       QUERYNO 254                                                01510000
001520     END-EXEC                                                     01520000
001530                                                                  01530000
001540     EXEC SQL DECLARE DZEVEFC1 CURSOR WITH HOLD FOR               01540000
001550       SELECT CT_RKTEVPR_479EVEF                                  01550000
001560            , NR_IDGOOD_479EVEF                                   01560000
001570            , NR_ID_479EVEF                                       01570000
001580       FROM DZEVEFTV                                              01580000
001590       WHERE CT_RKTPROD_479BEFF = :DCLDZBEFFTV.CT-RKTPROD-479BEFF 01590000
001600         AND NR_IDSTOCK_479BEFF = :DCLDZBEFFTV.NR-IDSTOCK-479BEFF 01600000
001610         AND NR_CDSTK_479BEFF = :DCLDZBEFFTV.NR-CDSTK-479BEFF     01610000
001620         AND NS_DBSTK_479BEFF = :DCLDZBEFFTV.NS-DBSTK-479BEFF     01620000
001630       ORDER BY NR_ID_479EVEF DESC                                01630000
001640       FOR READ ONLY                                              01640000
001650       QUERYNO 255                                                01650000
001660     END-EXEC.                                                    01660000
001670                                                                  01670000
001680                                                                  01680000
001690*DB2 GENERATED WORKING STORAGE                                    01690000
001700 01  WS-DB2-GENERATED.                                            01700000
001710     10  CS-PROGRAM               PIC X(8)    VALUE 'VMDZ4302'.   01710000
001720     10  WS-NB-OUTPUT-COUNT       PIC 9(7)    COMP-3 VALUE ZEROES.01720000
001730                                                                  01730000
001740*DB2 GENERATED TIMESTAMP AND AUDIT WORKING STORAGE                01740000
001750 01  WS-TIMESTAMP-FIELDS.                                         01750000
001760     05 TS-SYSTEM.                                                01760000
001770        10  DA-SYS.                                               01770000
001780            15  DA-SYS-CCYY.                                      01780000
001790                20  CC            PIC X(2).                       01790000
001800                20  YY            PIC X(2).                       01800000
001810            15  MM                PIC X(2).                       01810000
001820            15  DD                PIC X(2).                       01820000
001830        10  HR-SYS.                                               01830000
001840            15  HH                PIC X(2).                       01840000
001850            15  MI                PIC X(2).                       01850000
001860            15  SS                PIC X(2).                       01860000
001870            15  TT                PIC X(2).                       01870000
001880     05 TS-TIMESTAMP.                                             01880000
001890        10  CC                    PIC X(2).                       01890000
001900        10  YY                    PIC X(2).                       01900000
001910        10  TE-MARKER1            PIC X             VALUE '-'.    01910000
001920        10  MM                    PIC X(2).                       01920000
001930        10  TE-MARKER2            PIC X             VALUE '-'.    01930000
001940        10  DD                    PIC X(2).                       01940000
001950        10  TE-MARKER3            PIC X             VALUE '-'.    01950000
001960        10  HH                    PIC X(2).                       01960000
001970        10  TE-MARKER4            PIC X             VALUE '.'.    01970000
001980        10  MI                    PIC X(2).                       01980000
001990        10  TE-MARKER5            PIC X             VALUE '.'.    01990000
002000        10  SS                    PIC X(2).                       02000000
002010        10  TE-MARKER6            PIC X             VALUE '.'.    02010000
002020        10  TT                    PIC X(2).                       02020000
002030        10  NNNN                  PIC 9(04)         VALUE 0.      02030000
002040                                                                  02040000
002050 LINKAGE SECTION.                                                 02050000
002060*-----------------------------------------------------------------02060000
002070 01  PARAM-DATONLY.                                               02070000
002080     03  LS-PARAM        PIC S9(4) COMP.                          02080000
002090     03  LS-DATE-IND     PIC X.                                   02090000
002100     03  LS-DA-DMY.                                               02100000
002110         05  DD          PIC 99.                                  02110000
002120         05  MM          PIC 99.                                  02120000
002130         05  YY          PIC 99.                                  02130000
002140/                                                                 02140000
002150*-----------------------------------------------------------------02150000
002160 PROCEDURE DIVISION USING PARAM-DATONLY.                          02160000
002170*-----------------------------------------------------------------02170000
002180*                                                                 02180000
002190* BEGINVERWERKING                                                 02190000
002200*                                                                 02200000
002210     PERFORM 600-GET-TIMESTAMP.                                   02210000
002220     IF LS-DATE-IND = '0'                                         02220000
002230        ACCEPT WS-DA-YMD FROM DATE                                02230000
002240        MOVE CORR WS-DA-YMD TO WS-DA-DMY                          02240000
002250     ELSE                                                         02250000
002260        MOVE LS-DA-DMY      TO WS-DA-DMY                          02260000
002270     END-IF                                                       02270000
002280     MOVE CORR WS-DA-DMY  TO WS-DA-CYMD.                          02280000
002290     MOVE YY OF WS-DA-DMY TO CCYY OF WS-DA-CYMD.                  02290000
002300*                                                                 02300000
002310     IF CCYY OF WS-DA-CYMD LESS 80                                02310000
002320        ADD 2000 TO CCYY OF WS-DA-CYMD                            02320000
002330     ELSE                                                         02330000
002340        ADD 1900 TO CCYY OF WS-DA-CYMD                            02340000
002350     END-IF                                                       02350000
002360*                                                                 02360000
002370     MOVE CS-PROGRAM TO PROGRAM-NAME.                             02370000
002380     IF ERROR-STATUS NOT = '0000'                                 02380000
002390        DISPLAY 'BIND RUN-UNIT MISLUKT '                          02390000
002400        DISPLAY 'ERROR-STATUS ' ERROR-STATUS                      02400000
002410        CALL USERABEN                                             02410000
002420     END-IF                                                       02420000
002430     IF ERROR-STATUS NOT = '0000'                                 02430000
002440        DISPLAY 'BIND VMBWCEF MISLUKT '                           02440000
002450        DISPLAY 'ERROR-STATUS ' ERROR-STATUS                      02450000
002460        CALL USERABEN                                             02460000
002470     END-IF                                                       02470000
002480     IF ERROR-STATUS NOT = '0000'                                 02480000
002490        DISPLAY 'BIND VMBEFF  MISLUKT '                           02490000
002500        DISPLAY 'ERROR-STATUS ' ERROR-STATUS                      02500000
002510        CALL USERABEN                                             02510000
002520     END-IF                                                       02520000
002530     IF ERROR-STATUS NOT = '0000'                                 02530000
002540        DISPLAY 'BIND VMBEVEF MISLUKT '                           02540000
002550        DISPLAY 'ERROR-STATUS ' ERROR-STATUS                      02550000
002560        CALL USERABEN                                             02560000
002570     END-IF                                                       02570000
002580     IF ERROR-STATUS NOT = '0000'                                 02580000
002590        DISPLAY 'READY AREA VMBEFF1 MISLUKT '                     02590000
002600        DISPLAY 'ERROR-STATUS ' ERROR-STATUS                      02600000
002610        CALL USERABEN                                             02610000
002620     END-IF                                                       02620000
002630     IF ERROR-STATUS NOT = '0000'                                 02630000
002640        DISPLAY 'READY AREA VMBWCEF MISLUKT '                     02640000
002650        DISPLAY 'ERROR-STATUS ' ERROR-STATUS                      02650000
002660        CALL USERABEN                                             02660000
002670     END-IF                                                       02670000
002680*                                                                 02680000
002690     OPEN INPUT  EMISSIONS-I                                      02690000
002700     OUTPUT EFFEKT-O.                                             02700000
002710*                                                                 02710000
002720     READ EMISSIONS-I INTO INPUT-RECORD                           02720000
002730        AT END MOVE 1 TO SW-EOF                                   02730000
002740     END-READ.                                                    02740000
002750*                                                                 02750000
002760     PERFORM VERWERK-EMISSIONS UNTIL SW-EOF = 1.                  02760000
002770*                                                                 02770000
002780     CLOSE EMISSIONS-I.                                           02780000
002790                                                                  02790000
002800 EFFEKT-O.                                                        02800000
002810*                                                                 02810000
002820     DISPLAY 'TOTAL OUTPUT RECORDS : ' WS-NB-OUTPUT-COUNT         02820000
002830                                                                  02830000
002840     STOP RUN.                                                    02840000
002850/                                                                 02850000
002860*-----------------------------------------------------------------02860000
002870 VERWERK-EMISSIONS.                                               02870000
002880*-----------------------------------------------------------------02880000
002890     MOVE CORR I-DA-UE TO WS-DA-UE                                02890000
002900*                                                                 02900000
002910*DB2-KEEP: VMBWCEF has no DB2 layout after conversion.            02910000
002920*DB2-KEEP MOVE SPACES       TO VMBWCEF                            02920000
002930     PERFORM CALL-VM9BC50T                                        02930000
002940     MOVE BC50O-NR-ID-SECU    TO CO-IDISSUS-479WCEF OF DCLDZWCEFTV02940000
002950     MOVE BC50O-NS-SEQ-IRMO   TO NS-IRMOS-479WCEF OF DCLDZWCEFTV  02950000
002960     MOVE BC50O-DA-UBSEC-ISSU TO DA-UBSECIS-479WCEF OF DCLDZWCEFTV02960000
002970*                                                                 02970000
002980*                                                                 02980000
002990     IF ERROR-STATUS NOT = '0000'                                 02990000
003000        DISPLAY 'VMBWCEF    ' VMBWCEF                             03000000
003010        DISPLAY 'ERROR-STATUS ' ERROR-STATUS                      03010000
003020        DISPLAY ' '                                               03020000
003030     END-IF                                                       03030000
003040     IF ERROR-STATUS = '0000'                                     03040000
003050        INITIALIZE DCLDZBEFFTV                                    03050000
003060        PERFORM 710-OPEN-DZBEFFC1.                                03060000
003070        PERFORM 720-FETCH-DZBEFFC1.                               03070000
003080     END-IF                                                       03080000
003090*                                                                 03090000
003100     PERFORM VERWERK-EFFEKT UNTIL ERROR-STATUS NOT = '0000'.      03100000
003110     PERFORM 730-CLOSE-DZBEFFC1.                                  03110000
003120*                                                                 03120000
003130     READ EMISSIONS-I INTO INPUT-RECORD                           03130000
003140        AT END MOVE 1 TO SW-EOF                                   03140000
003150     END-READ.                                                    03150000
003160/                                                                 03160000
003170*-----------------------------------------------------------------03170000
003180 VERWERK-EFFEKT.                                                  03180000
003190*-----------------------------------------------------------------03190000
003200     MOVE 0        TO LAATSTE-DA-CR-EVENT-PROD.                   03200000
003210     MOVE 0        TO LAATSTE-OPD.                                03210000
003220     MOVE '000000' TO LAATSTE-CI.                                 03220000
003230     MOVE 0        TO SW-168                                      03230000
003240     INITIALIZE DCLDZEVEFTV                                       03240000
003250     PERFORM 810-OPEN-DZEVEFC1.                                   03250000
003260     PERFORM 820-FETCH-DZEVEFC1.                                  03260000
003270     PERFORM NEXT-VMBEVEF UNTIL ERROR-STATUS NOT = '0000'.        03270000
003280     PERFORM 830-CLOSE-DZEVEFC1.                                  03280000
003290     IF SW-168 = 1                                                03290000
003300        PERFORM WRITE-REFFEKT-O                                   03300000
003310        ADD 1 TO WS-NB-OUTPUT-COUNT                               03310000
003320     END-IF.                                                      03320000
003330     PERFORM 720-FETCH-DZBEFFC1.                                  03330000
003340*                                                                 03340000
003350*-----------------------------------------------------------------03350000
003360                                                                  03360000
003370/                                                                 03370000
003380 WRITE-REFFEKT-O.                                                 03380000
003390     MOVE LAATSTE-CI         TO UIT-NR-CI                         03390000
003400     MOVE AM-CN-STOCK        TO UIT-AM-CN-STOCK                   03400000
003410     MOVE I-CO-INTERNE       TO UIT-CO-INTERNE                    03410000
003420     MOVE NR-ID-STOCK-CD     TO UIT-NR-ID-STOCK-CD                03420000
003430     MOVE BC50O-CO-CURR-SECU TO UIT-CO-DEVISE                     03430000
003440     WRITE REFFEKT-O     FROM UITREC.                             03440000
003450                                                                  03450000
003460 NEXT-VMBEVEF.                                                    03460000
003470*-----------------------------------------------------------------03470000
003480     MOVE NR-IDGOOD-479EVEF OF DCLDZEVEFTV TO HULP-NR-ID-GOOD     03480000
003490     IF CT-RKTEVPR-479EVEF OF DCLDZEVEFTV = '0168' AND            03490000
003500        CT-OPD = 91 AND DA-CR-EVENT-PROD < WS-DA-CYMD             03500000
003510                                                                  03510000
003520        MOVE WS-DA-UE TO WS-DA-UE-MIN-1MAAND                      03520000
003530        IF MM OF WS-DA-UE-MIN-1MAAND < 2                          03530000
003540           MOVE 12 TO MM OF WS-DA-UE-MIN-1MAAND                   03540000
003550           SUBTRACT 1 FROM CCYY OF WS-DA-UE-MIN-1MAAND            03550000
003560        ELSE                                                      03560000
003570           SUBTRACT 1 FROM MM   OF WS-DA-UE-MIN-1MAAND            03570000
003580        END-IF                                                    03580000
003590                                                                  03590000
003600        IF WS-DA-UE-MIN-1MAAND NOT > DA-CR-EVENT-PROD             03600000
003610           MOVE 1 TO SW-168                                       03610000
003620        END-IF                                                    03620000
003630     END-IF.                                                      03630000
003640*                                                                 03640000
003650     IF CT-RKTEVPR-479EVEF OF DCLDZEVEFTV = '0060' AND            03650000
003660        DA-CR-EVENT-PROD NOT < WS-DA-CYMD                         03660000
003670        CONTINUE                                                  03670000
003680     ELSE                                                         03680000
003690        IF CT-RKTEVPR-479EVEF OF DCLDZEVEFTV   = '0060' AND       03690000
003700           LAATSTE-DA-CR-EVENT-PROD = 0                           03700000
003710           MOVE 1      TO LAATSTE-DA-CR-EVENT-PROD                03710000
003720           MOVE NR-CI  TO LAATSTE-CI                              03720000
003730           MOVE CT-OPD TO LAATSTE-OPD                             03730000
003740        ELSE                                                      03740000
003750           IF CT-RKTEVPR-479EVEF OF DCLDZEVEFTV = '0092' AND      03750000
003760              HULP-DA-UB-TRANSF > LAATSTE-DA-CR-EVENT-PROD AND    03760000
003770              HULP-DA-UB-TRANSF < WS-DA-CYMD-N                    03770000
003780              MOVE HULP-DA-UB-TRANSF TO LAATSTE-DA-CR-EVENT-PROD  03780000
003790              MOVE NR-CI             TO LAATSTE-CI                03790000
003800           END-IF                                                 03800000
003810        END-IF                                                    03810000
003820     END-IF                                                       03820000
003830*                                                                 03830000
003840     PERFORM 820-FETCH-DZEVEFC1.                                  03840000
003850*-----------------------------------------------------------------03850000
003860 CALL-VM9BC50T.                                                   03860000
003870*-----------------------------------------------------------------03870000
003880     INITIALIZE WS-VM9BC50I.                                      03880000
003890     INITIALIZE WS-VM9BC50O.                                      03890000
003900     MOVE 'VM4BD302'   TO BC50I-NM-CALLER                         03900000
003910     MOVE 'VM9BC50T'   TO BC50I-NM-BB                             03910000
003920     MOVE 'P'          TO BC50I-CO-TRANSMISSION                   03920000
003930     MOVE 'QUERY001'   TO BC50I-NM-FUNCTION                       03930000
003940     MOVE '2'          TO BC50I-CO-CLE                            03940000
003950     MOVE I-CO-INTERNE TO BC50I-NR-CLE-NO-INTERNE                 03950000
003960     MOVE 'Y'          TO BC50I-CO-DONNEES-FIXES.                 03960000
003970     MOVE 'Y'          TO BC50I-CO-CONDITIONS-EMISSION.           03970000
003980     MOVE 'Y'          TO BC50I-CO-CONDITIONS-VENTE.              03980000
003990     MOVE WS-DA-CYMD   TO BC50I-DA-DEMANDE.                       03990000
004000     MOVE WS-VM9BC50I  TO WS-VM9BC50T.                            04000000
004010     CALL CS-VM9BC50T USING WS-VM9BC50T.                          04010000
004020     MOVE WS-VM9BC50T TO WS-VM9BC50O.                             04020000
004030                                                                  04030000
004040*DB2 GENERATED CURSOR OPEN FETCH CLOSE PARAGRAPHS              *  04040000
004050                                                                  04050000
004060 710-OPEN-DZBEFFC1.                                               04060000
004070D    DISPLAY '710-OPEN-DZBEFFC1.'                                 04070000
004080     MOVE 710 TO SQL-LOCATION                                     04080000
004090                                                                  04090000
004100     EXEC SQL                                                     04100000
004110       OPEN DZBEFFC1                                              04110000
004120     END-EXEC                                                     04120000
004130                                                                  04130000
004140     EVALUATE SQLCODE                                             04140000
004150       WHEN ZERO                                                  04150000
004160            SET DZBEFFC1-NOT-EOC TO TRUE                          04160000
004170       WHEN OTHER                                                 04170000
004180            DISPLAY 'ERROR WHILE OPENING CURSOR DZBEFFC1'         04180000
004190            PERFORM SQLERROR                                      04190000
004200     END-EVALUATE                                                 04200000
004210     .                                                            04210000
004220                                                                  04220000
004230 720-FETCH-DZBEFFC1.                                              04230000
004240D    DISPLAY '720-FETCH-DZBEFFC1.'                                04240000
004250     SET DZBEFFC1-NOT-EOC TO TRUE                                 04250000
004260     MOVE 720 TO SQL-LOCATION                                     04260000
004270                                                                  04270000
004280     EXEC SQL                                                     04280000
004290       FETCH DZBEFFC1                                             04290000
004300        INTO :DCLDZBEFFTV.CT-RKTPROD-479BEFF                      04300000
004310           , :DCLDZBEFFTV.NR-IDSTOCK-479BEFF                      04310000
004320           , :DCLDZBEFFTV.NR-CDSTK-479BEFF                        04320000
004330           , :DCLDZBEFFTV.NS-DBSTK-479BEFF                        04330000
004340     END-EXEC                                                     04340000
004350                                                                  04350000
004360     EVALUATE SQLCODE                                             04360000
004370       WHEN ZERO                                                  04370000
004380            PERFORM VERWERK-EFFEKT                                04380000
004390       WHEN 100                                                   04390000
004400            SET DZBEFFC1-EOC TO TRUE                              04400000
004410       WHEN OTHER                                                 04410000
004420            DISPLAY 'ERROR WHILE FETCHING CURSOR DZBEFFC1'        04420000
004430            DISPLAY 'CO-IDPRKB-STOCK  = ' CO-IDISSUS-479WCEF      04430000
004440                                          OF DCLDZWCEFTV          04440000
004450            DISPLAY 'NS-IRMO-STOCK    = ' NS-IRMOS-479WCEF        04450000
004460                                          OF DCLDZWCEFTV          04460000
004470            DISPLAY 'DA-UBSECIS-STOCK = ' DA-UBSECIS-479WCEF      04470000
004480                                          OF DCLDZWCEFTV          04480000
004490            PERFORM SQLERROR                                      04490000
004500     END-EVALUATE                                                 04500000
004510     .                                                            04510000
004520                                                                  04520000
004530 730-CLOSE-DZBEFFC1.                                              04530000
004540D    DISPLAY '730-CLOSE-DZBEFFC1.'                                04540000
004550     MOVE 730 TO SQL-LOCATION                                     04550000
004560                                                                  04560000
004570     EXEC SQL                                                     04570000
004580       CLOSE DZBEFFC1                                             04580000
004590     END-EXEC                                                     04590000
004600                                                                  04600000
004610     EVALUATE SQLCODE                                             04610000
004620       WHEN ZERO                                                  04620000
004630            CONTINUE                                              04630000
004640       WHEN OTHER                                                 04640000
004650            DISPLAY 'ERROR WHILE CLOSING CURSOR DZBEFFC1'         04650000
004660            PERFORM SQLERROR                                      04660000
004670     END-EVALUATE                                                 04670000
004680     .                                                            04680000
004690                                                                  04690000
004700 810-OPEN-DZEVEFC1.                                               04700000
004710D    DISPLAY '810-OPEN-DZEVEFC1.'                                 04710000
004720     MOVE 810 TO SQL-LOCATION                                     04720000
004730                                                                  04730000
004740     EXEC SQL                                                     04740000
004750       OPEN DZEVEFC1                                              04750000
004760     END-EXEC                                                     04760000
004770                                                                  04770000
004780     EVALUATE SQLCODE                                             04780000
004790       WHEN ZERO                                                  04790000
004800            SET DZEVEFC1-NOT-EOC TO TRUE                          04800000
004810       WHEN OTHER                                                 04810000
004820            DISPLAY 'ERROR WHILE OPENING CURSOR DZEVEFC1'         04820000
004830            PERFORM SQLERROR                                      04830000
004840     END-EVALUATE                                                 04840000
004850     .                                                            04850000
004860                                                                  04860000
004870 820-FETCH-DZEVEFC1.                                              04870000
004880D    DISPLAY '820-FETCH-DZEVEFC1.'                                04880000
004890     SET DZEVEFC1-NOT-EOC TO TRUE                                 04890000
004900     MOVE 820 TO SQL-LOCATION                                     04900000
004910                                                                  04910000
004920     EXEC SQL                                                     04920000
004930       FETCH DZEVEFC1                                             04930000
004940        INTO :DCLDZEVEFTV.CT-RKTEVPR-479EVEF                      04940000
004950           , :DCLDZEVEFTV.NR-IDGOOD-479EVEF                       04950000
004960           , :DCLDZEVEFTV.NR-ID-479EVEF                           04960000
004970     END-EXEC                                                     04970000
004980                                                                  04980000
004990     EVALUATE SQLCODE                                             04990000
005000       WHEN ZERO                                                  05000000
005010            PERFORM NEXT-VMBEVEF                                  05010000
005020       WHEN 100                                                   05020000
005030            SET DZEVEFC1-EOC TO TRUE                              05030000
005040       WHEN OTHER                                                 05040000
005050            DISPLAY 'ERROR WHILE FETCHING CURSOR DZEVEFC1'        05050000
005060            DISPLAY 'CT-RK-TPROD    = ' CT-RKTPROD-479BEFF        05060000
005070                                        OF DCLDZBEFFTV            05070000
005080            DISPLAY 'NR-ID-STOCK-R1 = ' NR-IDSTOCK-479BEFF        05080000
005090                                        OF DCLDZBEFFTV            05090000
005100            DISPLAY 'NR-CD-STOCK    = ' NR-CDSTK-479BEFF          05100000
005110                                        OF DCLDZBEFFTV            05110000
005120            DISPLAY 'NS-DB-STOCK    = ' NS-DBSTK-479BEFF          05120000
005130                                        OF DCLDZBEFFTV            05130000
005140            PERFORM SQLERROR                                      05140000
005150     END-EVALUATE                                                 05150000
005160     .                                                            05160000
005170                                                                  05170000
005180 830-CLOSE-DZEVEFC1.                                              05180000
005190D    DISPLAY '830-CLOSE-DZEVEFC1.'                                05190000
005200     MOVE 830 TO SQL-LOCATION                                     05200000
005210                                                                  05210000
005220     EXEC SQL                                                     05220000
005230       CLOSE DZEVEFC1                                             05230000
005240     END-EXEC                                                     05240000
005250                                                                  05250000
005260     EVALUATE SQLCODE                                             05260000
005270       WHEN ZERO                                                  05270000
005280            CONTINUE                                              05280000
005290       WHEN OTHER                                                 05290000
005300            DISPLAY 'ERROR WHILE CLOSING CURSOR DZEVEFC1'         05300000
005310            PERFORM SQLERROR                                      05310000
005320     END-EVALUATE                                                 05320000
005330     .                                                            05330000
005340                                                                  05340000
005350                                                                  05350000
005360 600-GET-TIMESTAMP.                                               05360000
005370D    DISPLAY '600-GET-TIMESTAMP.'                                 05370000
005380     MOVE FUNCTION CURRENT-DATE TO TS-SYSTEM.                     05380000
005390     MOVE CC OF TS-SYSTEM       TO CC OF TS-TIMESTAMP             05390000
005400     MOVE YY OF TS-SYSTEM       TO YY OF TS-TIMESTAMP             05400000
005410     MOVE MM OF TS-SYSTEM       TO MM OF TS-TIMESTAMP             05410000
005420     MOVE DD OF TS-SYSTEM       TO DD OF TS-TIMESTAMP             05420000
005430     MOVE HH OF TS-SYSTEM       TO HH OF TS-TIMESTAMP             05430000
005440     MOVE MI OF TS-SYSTEM       TO MI OF TS-TIMESTAMP             05440000
005450     MOVE SS OF TS-SYSTEM       TO SS OF TS-TIMESTAMP             05450000
005460     MOVE TT OF TS-SYSTEM       TO TT OF TS-TIMESTAMP             05460000
005470     DISPLAY 'TIMESTAMP: ' TS-TIMESTAMP                           05470000
005480     .                                                            05480000
005490                                                                  05490000
005500*SQLERROR ROUTINE.                                                05500000
005510     EXEC SQL                                                     05510000
005520          INCLUDE SQLERROR                                        05520000
005530     END-EXEC.                                                    05530000
