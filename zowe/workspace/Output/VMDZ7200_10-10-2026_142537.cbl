000010 IDENTIFICATION DIVISION.                                         00010000
000020*========================                                         00020000
000030 PROGRAM-ID. VMDZ7200.                                            00030000
000040 AUTHOR.       Veerapandian.                                      00040000
000050                                                                  00050000
000060******************************************************************00060000
000070*                                                                 00070000
000080*    ARCHIVAGE :  EXTRACT DES FORMULAIRES A ARCHIVER              00080000
000090*    =========    (SOUSCRIPTIONS ET ANNULATIONS SOUSCRIPTIONS)    00090000
000100*                                                                 00100000
000110* WULTEPUTTE KRISTINE : (10/7/91) :                               00110000
000120*                                                                 00120000
000130* TOEVOEGEN VAN NIEUWE PLAGES VOOR BCI1                           00130000
000140*                                                                 00140000
000150* DE SCHEPPER KOEN    : (18/12/92) :                              00150000
000160*                                                                 00160000
000170* AANPASSING VOOR SLIK : UITBREIDING FORM 270 -> 390              00170000
000180*                                                                 00180000
000190* CLEMENT J. (06/93) : TOEVOEGEN PLAGES                           00190000
000200*                                                                 00200000
000210* DE SCHEPPER KOEN     (04/02/94) :                               00210000
000220*    PROGRAMMA VOLLEDIG HERSCHREVEN : GEEN SELECTIE OP            00220000
000230*    WAARDECODE MEER.                                             00230000
000240*                                                                 00240000
000250* POMPONIO S (03/97)                                              00250000
000260*    AANPASSING EURO2000 : PARMDATE EN 8 POSITIONS                00260000
000270*                          RECORD VMBFAS 388 -> 432 BYTES         00270000
000280*                                                                 00280000
000290* J-M BOOGAERTS 2005/02                                           00290000
000300 000300*    INTÉGRATION ARCHIVAGE IUNS P8                         00300000
000310*                                                                 00310000
000320******************************************************************00320000
000330                                                                  00330000
000340 ENVIRONMENT DIVISION.                                            00340000
000350*=====================                                            00350000
000360 CONFIGURATION SECTION.                                           00360000
000370*----------------------                                           00370000
000380 SPECIAL-NAMES.                                                   00380000
000390     DECIMAL-POINT IS COMMA.                                      00390000
000400*                                                                 00400000
000410 INPUT-OUTPUT SECTION.                                            00410000
000420*---------------------                                            00420000
000430 FILE-CONTROL.                                                    00430000
000440     SELECT DAARCH   ASSIGN TO UT-S-DD005.                        00440000
000450     SELECT FORM     ASSIGN TO UT-S-DD010.                        00450000
000460*                                                                 00460000
000470*---------------------                                            00470000
000480/                                                                 00480000
000490 DATA DIVISION.                                                   00490000
000500*==============                                                   00500000
000510 FILE SECTION.                                                    00510000
000520*-------------                                                    00520000
000530*    ----- DATE ARCHIVAGE -----                                   00530000
000540*                                                                 00540000
000550 FD  DAARCH     RECORDING F                                       00550000
000560                RECORD CONTAINS 20                                00560000
000570                BLOCK CONTAINS 0                                  00570000
000580                LABEL RECORD STANDARD.                            00580000
000590 01  DAARCH-REC                PIC X(20).                         00590000
000600*                                                                 00600000
000610*    ----- GESELECTEERDE FORMULIEREN -----                        00610000
000620*                                                                 00620000
000630 FD  FORM       RECORDING F                                       00630000
000640                RECORD CONTAINS 530                               00640000
000650                BLOCK CONTAINS 0                                  00650000
000660                LABEL RECORD STANDARD.                            00660000
000670 01  FORM-REC                  PIC X(530).                        00670000
000680/                                                                 00680000
000690*---------------                                                  00690000
000700*                                                                 00700000
000710 WORKING-STORAGE SECTION.                                         00710000
000720*------------------------                                         00720000
000730*                                                                 00730000
000740 77  USERABEN                  PIC X(8)   VALUE 'USERABEN'.       00740000
000750 77  WS-TELLER                 PIC S9(11) VALUE ZERO.             00750000
000760*                                                                 00760000
000770 01  W-NR-IS-FORM-AS           PIC 9(9).                          00770000
000780 01  FILLER REDEFINES W-NR-IS-FORM-AS.                            00780000
000790     05  W-NR-ID-ISSUE         PIC 9(7).                          00790000
000800     05  W-NR-CD-ISSUE         PIC 9(2).                          00800000
000810*                                                                 00810000
000820 01  REC-FORM.                                                    00820000
000830     05  F-FORM.                                                  00830000
000840*DB2 MATERIALISED IDMS RECORD VMBFAS                              00840000
000850       06  VMBFAS.                                                00850000
000860         07  KY-VMBFAS.                                           00860000
000870           08  NR-RK-GOOD-V02.                                    00870000
000880             09  CT-RK-TGDSERV.                                   00880000
000890               10  CT-RK-TGDSV             PIC X(4).              00890000
000900               10  CT-RK-TGOOD    REDEFINES CT-RK-TGDSV           00900000
000910                   PIC 9(4) VALUE ZEROES.                         00910000
000920             09  GR-ID-GOOD-V02.                                  00920000
000930               10  NR-CIO-FORM-AS          PIC 9(8) VALUE ZEROES. 00930000
000940               10  DA-CR-FORM-AS           PIC 9(8) VALUE ZEROES. 00940000
000950               10  NR-ID-FORM-AS           PIC 9(6) VALUE ZEROES. 00950000
000960               10  CT-OP-FORM-AS.                                 00960000
000970                 11  CT-OPD-FORM-AS        PIC S9(3) VALUE ZEROES.00970000
000980                 11  CT-OPG-FORM-AS         PIC 9(3) VALUE ZEROES.00980000
000990               10  FILLER                  PIC X(2).              00990000
001000         07  AT-FORM-AS.                                          01000000
001010           08  NR-CIW-FORM-AS          PIC X(8).                  01010000
001020           08  DA-VA-FORM-AS.                                     01020000
001030             09  DA-VA-FORM-AS-Y         PIC 9(4) VALUE ZEROES.   01030000
001040             09  DA-VA-FORM-AS-M         PIC 9(2) VALUE ZEROES.   01040000
001050             09  DA-VA-FORM-AS-D         PIC 9(2) VALUE ZEROES.   01050000
001060           08  CO-VM-FORM-AS           PIC X(1).                  01060000
001070           08  NR-IS-FORM-AS           PIC 9(9) VALUE ZEROES.     01070000
001080           08  RA-RT-FORM-AS          PIC S9(3)V9(3) VALUE ZEROES.01080000
001090           08  RA-CP-FORM-AS          PIC S9(3)V9(3) VALUE ZEROES.01090000
001100           08  RA-BASE-FORM-AS        PIC S9(3)V9(3) VALUE ZEROES.01100000
001110           08  DA-UB-FORM-AS.                                     01110000
001120             09  DA-UB-FORM-AS-Y         PIC 9(4) VALUE ZEROES.   01120000
001130             09  DA-UB-FORM-AS-M         PIC 9(2) VALUE ZEROES.   01130000
001140             09  DA-UB-FORM-AS-D         PIC 9(2) VALUE ZEROES.   01140000
001150           08  DA-UE-FORM-AS.                                     01150000
001160             09  DA-UE-FORM-AS-Y         PIC 9(4) VALUE ZEROES.   01160000
001170             09  DA-UE-FORM-AS-M         PIC 9(2) VALUE ZEROES.   01170000
001180             09  DA-UE-FORM-AS-D         PIC 9(2) VALUE ZEROES.   01180000
001190           08  DU-ST-FORM-AS           PIC 9(3) VALUE ZEROES.     01190000
001200           08  RA-PS-FORM-AS          PIC S9(3)V9(3) VALUE ZEROES.01200000
001210           08  RA-PR-FORM-AS          PIC S9(3)V9(3) VALUE ZEROES.01210000
001220           08  AM-CNS-FORM-AS          PIC S9(13)V99 VALUE ZEROES.01220000
001230           08  AM-PS-FORM-AS           PIC S9(13)V99 VALUE ZEROES.01230000
001240           08  NB-FI-FORM-AS           PIC 9(3) VALUE ZEROES.     01240000
001250           08  AM-FIN-FORM-AS          PIC S9(13)V99 VALUE ZEROES.01250000
001260           08  CO-RI-FORM-AS           PIC X(1).                  01260000
001270           08  NR-IDR-FORM-AS          PIC 9(6) VALUE ZEROES.     01270000
001280           08  DA-UER-FORM-AS.                                    01280000
001290             09  DA-UER-FORM-AS-Y        PIC 9(4) VALUE ZEROES.   01290000
001300             09  DA-UER-FORM-AS-M        PIC 9(2) VALUE ZEROES.   01300000
001310             09  DA-UER-FORM-AS-D        PIC 9(2) VALUE ZEROES.   01310000
001320           08  AM-FBA-FORM-AS          PIC S9(13)V99 VALUE ZEROES.01320000
001330           08  AM-FBB-FORM-AS          PIC S9(13)V99 VALUE ZEROES.01330000
001340           08  CO-RM-FORM-AS           PIC X(1).                  01340000
001350           08  RA-FB-FORM-AS          PIC S9(3)V9(3) VALUE ZEROES.01350000
001360           08  NB-FB-FORM-AS           PIC 9(2) VALUE ZEROES.     01360000
001370           08  AM-FBN-FORM-AS          PIC S9(13)V99 VALUE ZEROES.01370000
001380           08  RA-TI-FORM-AS           PIC 9(2)V9(2) VALUE ZEROES.01380000
001390           08  AM-CND-FORM-AS          PIC S9(13)V99 VALUE ZEROES.01390000
001400           08  AM-CNDN-FORM-AS         PIC S9(13)V99 VALUE ZEROES.01400000
001410           08  AM-CNSN-FORM-AS         PIC S9(13)V99 VALUE ZEROES.01410000
001420           08  NR-CD-FORM-AS           PIC 9(4) VALUE ZEROES.     01420000
001430           08  CT-SL-FORM-AS           PIC X(1).                  01430000
001440           08  NR-ST-FORM-AS           PIC 9(13) VALUE ZEROES.    01440000
001450           08  CX-TW-FORM-AS           PIC X(1).                  01450000
001460           08  NR-DS-FORM-AS           PIC 9(12) VALUE ZEROES.    01460000
001470           08  NR-IDX-FORM-AS          PIC 9(6) VALUE ZEROES.     01470000
001480           08  CO-LA-FORM-AS           PIC X(1).                  01480000
001490           08  AM-INTER-FORM-AS        PIC S9(13)V99 VALUE ZEROES.01490000
001500           08  NB-GROUP-FORM-AS        PIC 9(3) VALUE ZEROES.     01500000
001510           08  NR-PRGRP-FORM-AS        PIC 9(6) VALUE ZEROES.     01510000
001520           08  NR-NEGRP-FORM-AS        PIC 9(6) VALUE ZEROES.     01520000
001530           08  NR-FIGRP-FORM-AS        PIC 9(6) VALUE ZEROES.     01530000
001540           08  NR-SEGRP-FORM-AS        PIC 9(3) VALUE ZEROES.     01540000
001550         07  NS-IDCP-FORM-AS         PIC 9(3) VALUE ZEROES.       01550000
001560         07  AM-CNSSP-FORM-AS        PIC S9(13)V99 VALUE ZEROES.  01560000
001570         07  RA-CPTOT-FORM-AS        PIC S9(3)V9(3) VALUE ZEROES. 01570000
001580         07  CO-CP-FORM-AS           PIC X.                       01580000
001590         07  CO-PERIN-FORM-AS        PIC X.                       01590000
001600         07  NS-ID-FORM-AS           PIC 9(2) VALUE ZEROES.       01600000
001610         07  CO-DEV-FORM-AS          PIC X(3).                    01610000
001620         07  NB-KRDEV-FORM-AS        PIC S9(6)V9(5) VALUE ZEROES. 01620000
001630         07  AM-BSDEV-FORM-AS        PIC S9(13)V99 VALUE ZEROES.  01630000
001640         07  CO-TYP-FORM-AS          PIC X(3).                    01640000
001650         07  CO-SUBTP-FORM-AS        PIC X(3).                    01650000
001660         07  CO-CONT-FORM-AS         PIC X(3).                    01660000
001670         07  CO-TPVGL-FORM-AS        PIC X(2).                    01670000
001680         07  AM-VGL-FORM-AS          PIC S9(13)V99 VALUE ZEROES.  01680000
001690         07  NR-PROD-FORM-AS         PIC X(4).                    01690000
001700         07  DA-ACTVR-FORM-AS.                                    01700000
001710           08  DY-ACTVR-FORM-AS        PIC 9(4) VALUE ZEROES.     01710000
001720           08  DM-ACTVR-FORM-AS        PIC 9(2) VALUE ZEROES.     01720000
001730           08  DD-ACTVR-FORM-AS        PIC 9(2) VALUE ZEROES.     01730000
001740         07  DA-INVTR-FORM-AS.                                    01740000
001750           08  DY-INVTR-FORM-AS        PIC 9(4) VALUE ZEROES.     01750000
001760           08  DM-INVTR-FORM-AS        PIC 9(2) VALUE ZEROES.     01760000
001770           08  DD-INVTR-FORM-AS        PIC 9(2) VALUE ZEROES.     01770000
001780         07  RA-QZTTI-FORM-AS        PIC S9(3)V999 VALUE ZEROES.  01780000
001790         07  RA-DGTTI-FORM-AS        PIC S9(3)V9(3) VALUE ZEROES. 01790000
001800         07  NB-DGTTI-FORM-AS        PIC 9(2) VALUE ZEROES.       01800000
001810         07  AM-DGTTI-FORM-AS        PIC S9(13)V99 VALUE ZEROES.  01810000
001820         07  ST-DGTTI-FORM-AS        PIC 9(1) VALUE ZEROES.       01820000
001830         07  ST-PRRW-FORM-AS         PIC 9(1) VALUE ZEROES.       01830000
001840         07  RA-GIFT-FORM-AS         PIC S9(3)V9(3) VALUE ZEROES. 01840000
001850         07  AM-GIFT-FORM-AS         PIC S9(13)V99 VALUE ZEROES.  01850000
001860         07  ST-VOORH-FORM-AS        PIC 9(1) VALUE ZEROES.       01860000
001870         07  DA-CPTA-FORM-AS.                                     01870000
001880           08  DY-CPTA-FORM-AS         PIC 9(4) VALUE ZEROES.     01880000
001890           08  DM-CPTA-FORM-AS         PIC 9(2) VALUE ZEROES.     01890000
001900           08  DD-CPTA-FORM-AS         PIC 9(2) VALUE ZEROES.     01900000
001910         07  CO-EXTOB-FORM-AS        PIC X(1).                    01910000
001920         07  CO-PLTOB-FORM-AS        PIC X(1).                    01920000
001930         07  RA-TOB-FORM-AS          PIC S9(3)V9(3) VALUE ZEROES. 01930000
001940         07  AM-TOB-FORM-AS          PIC S9(13)V99 VALUE ZEROES.  01940000
001950         07  RA-TARPH-FORM-AS        PIC S9(3)V9(3) VALUE ZEROES. 01950000
001960         07  AM-TARPH-FORM-AS        PIC S9(13)V99 VALUE ZEROES.  01960000
001970         07  AM-BASE-FORM-AS         PIC S9(13)V99 VALUE ZEROES.  01970000
001980         07  AM-FLK-FORM-AS          PIC S9(3)V9(2) VALUE ZEROES. 01980000
001990         07  FILLER                  PIC X(0014).                 01990000
002000     05  F-SW-ARCH             PIC X.                             02000000
002010     05  F-SW-VMBFGD           PIC X.                             02010000
002020     05  F-TELLER              PIC 9(11) VALUE ZEROES.            02020000
002030     05  F-NR-IS               PIC 9(7).                          02030000
002040     05  F-NR-ST               PIC 9(13).                         02040000
002050*                                                                 02050000
002060 COPY VMDZ270I.                                                   02060000
002070*                                                                 02070000
002080 01  WS-DATUMS.                                                   02080000
002090     02  DATE-YMD.                                                02090000
002100         03  D-YEAR            PIC 9(2).                          02100000
002110         03  D-MONTH           PIC 9(2).                          02110000
002120         03  D-DAY             PIC 9(2).                          02120000
002130     02  DATE-YMD8.                                               02130000
002140         03  D-CENT            PIC 9(2).                          02140000
002150         03  D-YEAR            PIC 9(2).                          02150000
002160         03  D-MONTH           PIC 9(2).                          02160000
002170         03  D-DAY             PIC 9(2).                          02170000
002180     02  DATE-DMY8.                                               02180000
002190         03  D-DAY             PIC 9(2).                          02190000
002200         03  D-MONTH           PIC 9(2).                          02200000
002210         03  D-CENT            PIC 9(2).                          02210000
002220         03  D-YEAR            PIC 9(2).                          02220000
002230*                                                                 02230000
002240/                                                                 02240000
002250*                                                                 02250000
002260*                                                                 02260000
002270*                                                                 02270000
002280*                                                                 02280000
002290*                                                                 02290000
002300*                                                                 02300000
002310/                                                                 02310000
002320                                                                  02320000
002330*DB2 INFRASTRUCTURE - SQLCA, INCLUDES, FLAGS                   *  02330000
002340     EXEC SQL INCLUDE SQLERRWS END-EXEC.                          02340000
002350     EXEC SQL INCLUDE SQLCA END-EXEC.                             02350000
002360     EXEC SQL INCLUDE DZBFASTV END-EXEC.                          02360000
002370     EXEC SQL INCLUDE DZSIASTV END-EXEC.                          02370000
002380                                                                  02380000
002390*DB2 CURSOR END-OF-CURSOR FLAGS                                *  02390000
002400 01  WS-DZBFASC1-FLAG               PIC X.                        02400000
002410     88  DZBFASC1-NOT-EOC           VALUE 'N'.                    02410000
002420     88  DZBFASC1-EOC               VALUE 'Y'.                    02420000
002430                                                                  02430000
002440                                                                  02440000
002450*DB2 CURSOR DECLARATIONS                                       *  02450000
002460     EXEC SQL                                                     02460000
002470       DECLARE DZBFASC1 CURSOR WITH HOLD FOR                      02470000
002480       SELECT                                                     02480000
002490         DA_CPTAFS_479BFAS                                        02490000
002500        , DA_CRFMAS_479BFAS                                       02500000
002510        , NR_ISFMAS_479BFAS                                       02510000
002520        , NR_STFMAS_479BFAS                                       02520000
002530        , CT_RKTGDSV_479BFAS                                      02530000
002540        , NR_CIOFMAS_479BFAS                                      02540000
002550        , NR_IDFMAS_479BFAS                                       02550000
002560        , CT_OPD_479BFAS                                          02560000
002570        , CT_OPG_479BFAS                                          02570000
002580        , NR_CIWFMAS_479BFAS                                      02580000
002590        , DA_VAFMAS_479BFAS                                       02590000
002600        , CO_VMFMAS_479BFAS                                       02600000
002610        , RA_RTFMAS_479BFAS                                       02610000
002620        , RA_CPFMAS_479BFAS                                       02620000
002630        , RA_BASFMAS_479BFAS                                      02630000
002640        , DA_UBFMAS_479BFAS                                       02640000
002650        , DA_UEFMAS_479BFAS                                       02650000
002660        , DU_STFMAS_479BFAS                                       02660000
002670        , RA_PSFMAS_479BFAS                                       02670000
002680        , RA_PRFMAS_479BFAS                                       02680000
002690        , AM_CNSFMAS_479BFAS                                      02690000
002700        , AM_PSFMAS_479BFAS                                       02700000
002710        , NB_FIFMAS_479BFAS                                       02710000
002720        , AM_FINFMAS_479BFAS                                      02720000
002730        , CO_RIFMAS_479BFAS                                       02730000
002740        , NR_IDRFMAS_479BFAS                                      02740000
002750        , DA_UERFMAS_479BFAS                                      02750000
002760        , AM_FBAFMAS_479BFAS                                      02760000
002770        , AM_FBBFMAS_479BFAS                                      02770000
002780        , CO_RMFMAS_479BFAS                                       02780000
002790        , RA_FBFMAS_479BFAS                                       02790000
002800        , NB_FBFMAS_479BFAS                                       02800000
002810        , AM_FBNFMAS_479BFAS                                      02810000
002820        , RA_TIFMAS_479BFAS                                       02820000
002830        , AM_CNDFMAS_479BFAS                                      02830000
002840        , AM_CNDNFAS_479BFAS                                      02840000
002850        , AM_CNSNFAS_479BFAS                                      02850000
002860        , NR_CDFMAS_479BFAS                                       02860000
002870        , CT_SLFMAS_479BFAS                                       02870000
002880        , CX_TWFMAS_479BFAS                                       02880000
002890        , NR_DSFMAS_479BFAS                                       02890000
002900        , NR_IDXFMAS_479BFAS                                      02900000
002910        , CO_LAFMAS_479BFAS                                       02910000
002920        , AM_INTFMAS_479BFAS                                      02920000
002930        , NB_GRPFMAS_479BFAS                                      02930000
002940        , NR_PRGRPFS_479BFAS                                      02940000
002950        , NR_NEGRPFS_479BFAS                                      02950000
002960        , NR_FIGRPFS_479BFAS                                      02960000
002970        , NR_SEGRPFS_479BFAS                                      02970000
002980        , NS_IDCPFS_479BFAS                                       02980000
002990        , AM_CNSSPFS_479BFAS                                      02990000
003000        , RA_CPTOTFS_479BFAS                                      03000000
003010        , CO_CPFMAS_479BFAS                                       03010000
003020        , CO_PERINFS_479BFAS                                      03020000
003030        , NS_IDFMAS_479BFAS                                       03030000
003040        , CO_DEVFMAS_479BFAS                                      03040000
003050        , NB_KRDEVFS_479BFAS                                      03050000
003060        , AM_BSDECFS_479BFAS                                      03060000
003070        , CO_TYPFMAS_479BFAS                                      03070000
003080        , CO_SUBTPFS_479BFAS                                      03080000
003090        , CO_CONTFS_479BFAS                                       03090000
003100        , CO_TPVGLFS_479BFAS                                      03100000
003110        , AM_VGLFMAS_479BFAS                                      03110000
003120        , NR_PRDFMAS_479BFAS                                      03120000
003130        , DA_ACTVRFS_479BFAS                                      03130000
003140        , DA_INVTRFS_479BFAS                                      03140000
003150        , RA_QZTTIFS_479BFAS                                      03150000
003160        , RA_DGTTIFS_479BFAS                                      03160000
003170        , NB_DGTTIFS_479BFAS                                      03170000
003180        , AM_DGTTIFS_479BFAS                                      03180000
003190        , ST_DGTTIFS_479BFAS                                      03190000
003200        , ST_PRRWFS_479BFAS                                       03200000
003210        , RA_GIFTFS_479BFAS                                       03210000
003220        , AM_GIFTFS_479BFAS                                       03220000
003230        , ST_VOORHFS_479BFAS                                      03230000
003240        , CO_EXTOBFS_479BFAS                                      03240000
003250        , CO_PLTOBFS_479BFAS                                      03250000
003260        , RA_TOBFS_479BFAS                                        03260000
003270        , AM_TOBFS_479BFAS                                        03270000
003280        , RA_TARPHFS_479BFAS                                      03280000
003290        , AM_TARPH_479BFAS                                        03290000
003300        , AM_BASEFS_479BFAS                                       03300000
003310        , AM_FLKFS_479BFAS                                        03310000
003320        , NR_CIOFMAS_479SIAS                                      03320000
003330        , NR_IDFMAS_479SIAS                                       03330000
003340        , NR_ID_479BFAS                                           03340000
003350       FROM DZBFASTV                                              03350000
003360       WHERE                                                      03360000
003370         NR_CIOFMAS_479SIAS = :DCLDZSIASTV.NR-CIOFMAS-479SIAS     03370000
003380         AND NR_IDFMAS_479SIAS = :DCLDZSIASTV.NR-IDFMAS-479SIAS   03380000
003390       ORDER BY                                                   03390000
003400         NR_ID_479BFAS ASC                                        03400000
003410       FOR READ ONLY                                              03410000
003420       QUERYNO 254                                                03420000
003430     END-EXEC.                                                    03430000
003440                                                                  03440000
003450*DB2 DATE CONVERSION WORKING STORAGE                              03450000
003460 01  WS-DATUMVELDEN.                                              03460000
003470     03  DA-CCYYMMDD.                                             03470000
003480         05  CC                    PIC 99       VALUE ZERO.       03480000
003490         05  YY                    PIC 99       VALUE ZERO.       03490000
003500         05  MM                    PIC 99       VALUE ZERO.       03500000
003510         05  DD                    PIC 99       VALUE ZERO.       03510000
003520     03  DA-CCYYMMDD-R REDEFINES DA-CCYYMMDD.                     03520000
003530         05  CCYY                  PIC 9999.                      03530000
003540         05  MM                    PIC 99.                        03540000
003550         05  DD                    PIC 99.                        03550000
003560     03  DA-DD-MM-CCYY.                                           03560000
003570         05  DD                    PIC 9(02).                     03570000
003580         05  TE-MARKER5            PIC X        VALUE '.'.        03580000
003590         05  MM                    PIC 9(02).                     03590000
003600         05  TE-MARKER6            PIC X        VALUE '.'.        03600000
003610         05  CCYY                  PIC 9(04).                     03610000
003620     02  HELP-DA-CPTAFS-479BFAS         PIC 9(8)     VALUE ZEROES.03620000
003630     02  HELP-DA-CRFMAS-479BFAS         PIC 9(8)     VALUE ZEROES.03630000
003640                                                                  03640000
003650                                                                  03650000
003660*DB2 GENERATED TIMESTAMP AND AUDIT WORKING STORAGE                03660000
003670 77  CS-PROGRAM               PIC X(8)    VALUE 'VMDZ7200'.       03670000
003680 01 WS-TIMESTAMP-FIELDS.                                          03680000
003690     05 TS-SYSTEM.                                                03690000
003700        10  CC                  PIC X(2).                         03700000
003710        10  YY                  PIC X(2).                         03710000
003720        10  MM                  PIC X(2).                         03720000
003730        10  DD                  PIC X(2).                         03730000
003740        10  HH                  PIC X(2).                         03740000
003750        10  MI                  PIC X(2).                         03750000
003760        10  SS                  PIC X(2).                         03760000
003770        10  TT                  PIC X(2).                         03770000
003780        10  FILLER              PIC X(13).                        03780000
003790     05 TS-TIMESTAMP.                                             03790000
003800        10  CC                  PIC X(2).                         03800000
003810        10  YY                  PIC X(2).                         03810000
003820        10  TE-MARKER1          PIC X    VALUE '-'.               03820000
003830        10  MM                  PIC X(2).                         03830000
003840        10  TE-MARKER2          PIC X    VALUE '-'.               03840000
003850        10  DD                  PIC X(2).                         03850000
003860        10  TE-MARKER3          PIC X    VALUE '-'.               03860000
003870        10  HH                  PIC X(2).                         03870000
003880        10  TE-MARKER4          PIC X    VALUE '.'.               03880000
003890        10  MI                  PIC X(2).                         03890000
003900        10  TE-MARKER5          PIC X    VALUE '.'.               03900000
003910        10  SS                  PIC X(2).                         03910000
003920        10  TE-MARKER6          PIC X    VALUE '.'.               03920000
003930        10  TT                  PIC X(2).                         03930000
003940        10  NNNN                PIC 9(04) VALUE 0.                03940000
003950                                                                  03950000
003960                                                                  03960000
003970*DB2 GENERATED ROW COUNTERS                                       03970000
003980 01  WS-DB2-COUNTERS.                                             03980000
003990     10  WS-NB-BFAS-COUNT         PIC 9(7)    COMP-3 VALUE ZEROES.03990000
004000 LINKAGE SECTION.                                                 04000000
004010 01  PARAM-ZONEDO.                                                04010000
004020     02  L-PARAM          PIC S9(4)   COMP.                       04020000
004030     02  DATUMLS.                                                 04030000
004040         03  DATE-IND     PIC X.                                  04040000
004050         03  DATE8-LS     PIC 9(8).                               04050000
004060/                                                                 04060000
004070 PROCEDURE DIVISION USING PARAM-ZONEDO.                           04070000
004080 100-INITIALIZE.                                                  04080000
004090*DB2: Centralized initialization (all DCLGEN groups, constants, ti04090000
004100*DB2: Redundant INITIALIZE block removed (consolidated in 100-INIT04100000
004110     MOVE CS-PROGRAM   TO PROGRAM-NAME.                           04110000
004120     PERFORM 600-GET-TIMESTAMP.                                   04120000
004130     .                                                            04130000
004140                                                                  04140000
004150                                                                  04150000
004160*======================================                           04160000
004170     PERFORM 600-GET-TIMESTAMP.                                   04170000
004180     PERFORM BEGIN-PROGRAMMA THRU BEGIN-PROGRAMMA-EXIT.           04180000
004190     PERFORM BEHANDELING THRU BEHANDELING-EXIT                    04190000
004200     UNTIL DZBFASC1-EOC.                                          04200000
004210     PERFORM 730-CLOSE-DZBFASC1.                                  04210000
004220     PERFORM EINDE-PROGRAMMA THRU EINDE-PROGRAMMA-EXIT.           04220000
004230*                                                                 04230000
004240     DISPLAY 'TOTAL BFAS RECORDS   : ' WS-NB-BFAS-COUNT           04240000
004250                                                                  04250000
004260     GOBACK.                                                      04260000
004270*                                                                 04270000
004280*                                                                 04280000
004290 BEGIN-PROGRAMMA.                                                 04290000
004300*----------------                                                 04300000
004310     IF DATE-IND = '0'                                            04310000
004320        ACCEPT DATE-YMD         FROM DATE                         04320000
004330        MOVE CORR DATE-YMD    TO DATE-DMY8                        04330000
004340        IF D-YEAR OF DATE-YMD > 60                                04340000
004350           MOVE 19            TO D-CENT OF DATE-DMY8              04350000
004360        ELSE                                                      04360000
004370           MOVE 20            TO D-CENT OF DATE-DMY8              04370000
004380        END-IF                                                    04380000
004390     ELSE                                                         04390000
004400        MOVE DATE8-LS         TO DATE-DMY8                        04400000
004410        MOVE CORR DATE-DMY8   TO DATE-YMD                         04410000
004420     END-IF.                                                      04420000
004430     MOVE CORR DATE-DMY8      TO DATE-YMD8.                       04430000
004440                                                                  04440000
004450*                                                                 04450000
004460     MOVE SPACES TO REC-FORM.                                     04460000
004470*                                                                 04470000
004480     OPEN INPUT  DAARCH                                           04480000
004490     OUTPUT FORM.                                                 04490000
004500     READ DAARCH INTO VMDZ270I-REC                                04500000
004510        AT END                                                    04510000
004520        DISPLAY 'VM7BD200: ** DATE ARCHIVAGE NOT OK **'           04520000
004530        CALL USERABEN.                                            04530000
004540        DISPLAY 'DATE ARCH : ' DA-ARCH-YMD.                       04540000
004550        CLOSE DAARCH.                                             04550000
004560*                                                                 04560000
004570        MOVE 'VMDZ7200'          TO PROGRAM-NAME.                 04570000
004580*                                                                 04580000
004590*DB2: Expanded LRF FIRST VMBTL03-R01 WHERE SWEEP-VMBFAS -> VMBFAS 04590000
004600*  WITHIN AR-VMBFRM1.                                             04600000
004610*DB2: Converted OBTAIN FIRST VMBFAS WITHIN AR-VMBFRM1.            04610000
004620        PERFORM 710-OPEN-DZBFASC1.                                04620000
004630        PERFORM 720-FETCH-DZBFASC1.                               04630000
004640*                                                                 04640000
004650 BEGIN-PROGRAMMA-EXIT.                                            04650000
004660*                                                                 04660000
004670     EXIT.                                                        04670000
004680*                                                                 04680000
004690*                                                                 04690000
004700 BEHANDELING.                                                     04700000
004710*------------                                                     04710000
004720*DB2: realigned 2 DB2 DATE host(s) before comparison.             04720000
004730     MOVE ZEROES TO DA-CCYYMMDD                                   04730000
004740     MOVE ZEROES TO HELP-DA-CPTAFS-479BFAS                        04740000
004750     MOVE DA-CPTAFS-479BFAS OF DCLDZBFASTV TO DA-DD-MM-CCYY       04750000
004760     EVALUATE TRUE                                                04760000
004770       WHEN DA-DD-MM-CCYY = '01.01.0001'                          04770000
004780            MOVE ZEROES TO DA-CCYYMMDD-R                          04780000
004790       WHEN DA-DD-MM-CCYY = '31.12.9999'                          04790000
004800            MOVE '99999999' TO DA-CCYYMMDD-R                      04800000
004810       WHEN OTHER                                                 04810000
004820            MOVE CCYY OF DA-DD-MM-CCYY TO CCYY OF DA-CCYYMMDD-R   04820000
004830            MOVE MM   OF DA-DD-MM-CCYY TO MM   OF DA-CCYYMMDD-R   04830000
004840            MOVE DD   OF DA-DD-MM-CCYY TO DD   OF DA-CCYYMMDD-R   04840000
004850     END-EVALUATE                                                 04850000
004860     MOVE DA-CCYYMMDD-R TO HELP-DA-CPTAFS-479BFAS                 04860000
004870     MOVE ZEROES TO DA-CCYYMMDD                                   04870000
004880     MOVE ZEROES TO HELP-DA-CRFMAS-479BFAS                        04880000
004890     MOVE DA-CRFMAS-479BFAS OF DCLDZBFASTV TO DA-DD-MM-CCYY       04890000
004900     EVALUATE TRUE                                                04900000
004910       WHEN DA-DD-MM-CCYY = '01.01.0001'                          04910000
004920            MOVE ZEROES TO DA-CCYYMMDD-R                          04920000
004930       WHEN DA-DD-MM-CCYY = '31.12.9999'                          04930000
004940            MOVE '99999999' TO DA-CCYYMMDD-R                      04940000
004950       WHEN OTHER                                                 04950000
004960            MOVE CCYY OF DA-DD-MM-CCYY TO CCYY OF DA-CCYYMMDD-R   04960000
004970            MOVE MM   OF DA-DD-MM-CCYY TO MM   OF DA-CCYYMMDD-R   04970000
004980            MOVE DD   OF DA-DD-MM-CCYY TO DD   OF DA-CCYYMMDD-R   04980000
004990     END-EVALUATE                                                 04990000
005000     MOVE DA-CCYYMMDD-R TO HELP-DA-CRFMAS-479BFAS                 05000000
005010     IF (HELP-DA-CPTAFS-479BFAS < DA-ARCH-YMD  AND                05010000
005020        HELP-DA-CPTAFS-479BFAS NOT = '00000000') OR               05020000
005030        (HELP-DA-CRFMAS-479BFAS < DA-ARCH-YMD AND                 05030000
005040        HELP-DA-CPTAFS-479BFAS = '00000000')                      05040000
005050        ADD 1              TO WS-TELLER                           05050000
005060        MOVE WS-TELLER     TO F-TELLER                            05060000
005070*DB2: Materialised VMBFAS from DCLDZBFASTV - 83 field move(s).    05070000
005080        MOVE CT-RKTGDSV-479BFAS OF DCLDZBFASTV TO                 05080000
005090        CT-RK-TGDSV OF VMBFAS                                     05090000
005100        MOVE NR-CIOFMAS-479BFAS OF DCLDZBFASTV TO                 05100000
005110        NR-CIO-FORM-AS OF VMBFAS                                  05110000
005120        MOVE DA-CRFMAS-479BFAS OF DCLDZBFASTV TO DA-DD-MM-CCYY    05120000
005130        EVALUATE TRUE                                             05130000
005140          WHEN DA-DD-MM-CCYY = '01.01.0001'                       05140000
005150               MOVE ZEROES TO DA-CCYYMMDD-R                       05150000
005160          WHEN DA-DD-MM-CCYY = '31.12.9999'                       05160000
005170               MOVE '99999999' TO DA-CCYYMMDD-R                   05170000
005180          WHEN OTHER                                              05180000
005190               MOVE CCYY OF DA-DD-MM-CCYY TO CCYY                 05190000
005200               OF DA-CCYYMMDD-R                                   05200000
005210               MOVE MM OF DA-DD-MM-CCYY TO MM OF DA-CCYYMMDD-R    05210000
005220               MOVE DD OF DA-DD-MM-CCYY TO DD OF DA-CCYYMMDD-R    05220000
005230        END-EVALUATE                                              05230000
005240        MOVE DA-CCYYMMDD-R TO DA-CR-FORM-AS OF VMBFAS             05240000
005250        MOVE NR-IDFMAS-479BFAS OF DCLDZBFASTV TO                  05250000
005260        NR-ID-FORM-AS OF VMBFAS                                   05260000
005270        MOVE CT-OPD-479BFAS OF DCLDZBFASTV TO                     05270000
005280        CT-OPD-FORM-AS OF VMBFAS                                  05280000
005290        MOVE CT-OPG-479BFAS OF DCLDZBFASTV TO                     05290000
005300        CT-OPG-FORM-AS OF VMBFAS                                  05300000
005310        MOVE NR-CIWFMAS-479BFAS OF DCLDZBFASTV TO                 05310000
005320        NR-CIW-FORM-AS OF VMBFAS                                  05320000
005330        MOVE DA-VAFMAS-479BFAS OF DCLDZBFASTV TO DA-DD-MM-CCYY    05330000
005340        EVALUATE TRUE                                             05340000
005350          WHEN DA-DD-MM-CCYY = '01.01.0001'                       05350000
005360               MOVE ZEROES TO DA-CCYYMMDD-R                       05360000
005370          WHEN DA-DD-MM-CCYY = '31.12.9999'                       05370000
005380               MOVE '99999999' TO DA-CCYYMMDD-R                   05380000
005390          WHEN OTHER                                              05390000
005400               MOVE CCYY OF DA-DD-MM-CCYY TO CCYY                 05400000
005410               OF DA-CCYYMMDD-R                                   05410000
005420               MOVE MM OF DA-DD-MM-CCYY TO MM OF DA-CCYYMMDD-R    05420000
005430               MOVE DD OF DA-DD-MM-CCYY TO DD OF DA-CCYYMMDD-R    05430000
005440        END-EVALUATE                                              05440000
005450        MOVE DA-CCYYMMDD-R TO DA-VA-FORM-AS OF VMBFAS             05450000
005460        MOVE CO-VMFMAS-479BFAS OF DCLDZBFASTV TO                  05460000
005470        CO-VM-FORM-AS OF VMBFAS                                   05470000
005480        MOVE NR-ISFMAS-479BFAS OF DCLDZBFASTV TO                  05480000
005490        NR-IS-FORM-AS OF VMBFAS                                   05490000
005500        MOVE RA-RTFMAS-479BFAS OF DCLDZBFASTV TO                  05500000
005510        RA-RT-FORM-AS OF VMBFAS                                   05510000
005520        MOVE RA-CPFMAS-479BFAS OF DCLDZBFASTV TO                  05520000
005530        RA-CP-FORM-AS OF VMBFAS                                   05530000
005540        MOVE RA-BASFMAS-479BFAS OF DCLDZBFASTV TO                 05540000
005550        RA-BASE-FORM-AS OF VMBFAS                                 05550000
005560        MOVE DA-UBFMAS-479BFAS OF DCLDZBFASTV TO DA-DD-MM-CCYY    05560000
005570        EVALUATE TRUE                                             05570000
005580          WHEN DA-DD-MM-CCYY = '01.01.0001'                       05580000
005590               MOVE ZEROES TO DA-CCYYMMDD-R                       05590000
005600          WHEN DA-DD-MM-CCYY = '31.12.9999'                       05600000
005610               MOVE '99999999' TO DA-CCYYMMDD-R                   05610000
005620          WHEN OTHER                                              05620000
005630               MOVE CCYY OF DA-DD-MM-CCYY TO CCYY                 05630000
005640               OF DA-CCYYMMDD-R                                   05640000
005650               MOVE MM OF DA-DD-MM-CCYY TO MM OF DA-CCYYMMDD-R    05650000
005660               MOVE DD OF DA-DD-MM-CCYY TO DD OF DA-CCYYMMDD-R    05660000
005670        END-EVALUATE                                              05670000
005680        MOVE DA-CCYYMMDD-R TO DA-UB-FORM-AS OF VMBFAS             05680000
005690        MOVE DA-UEFMAS-479BFAS OF DCLDZBFASTV TO DA-DD-MM-CCYY    05690000
005700        EVALUATE TRUE                                             05700000
005710          WHEN DA-DD-MM-CCYY = '01.01.0001'                       05710000
005720               MOVE ZEROES TO DA-CCYYMMDD-R                       05720000
005730          WHEN DA-DD-MM-CCYY = '31.12.9999'                       05730000
005740               MOVE '99999999' TO DA-CCYYMMDD-R                   05740000
005750          WHEN OTHER                                              05750000
005760               MOVE CCYY OF DA-DD-MM-CCYY TO CCYY                 05760000
005770               OF DA-CCYYMMDD-R                                   05770000
005780               MOVE MM OF DA-DD-MM-CCYY TO MM OF DA-CCYYMMDD-R    05780000
005790               MOVE DD OF DA-DD-MM-CCYY TO DD OF DA-CCYYMMDD-R    05790000
005800        END-EVALUATE                                              05800000
005810        MOVE DA-CCYYMMDD-R TO DA-UE-FORM-AS OF VMBFAS             05810000
005820        MOVE DU-STFMAS-479BFAS OF DCLDZBFASTV TO                  05820000
005830        DU-ST-FORM-AS OF VMBFAS                                   05830000
005840        MOVE RA-PSFMAS-479BFAS OF DCLDZBFASTV TO                  05840000
005850        RA-PS-FORM-AS OF VMBFAS                                   05850000
005860        MOVE RA-PRFMAS-479BFAS OF DCLDZBFASTV TO                  05860000
005870        RA-PR-FORM-AS OF VMBFAS                                   05870000
005880        MOVE AM-CNSFMAS-479BFAS OF DCLDZBFASTV TO                 05880000
005890        AM-CNS-FORM-AS OF VMBFAS                                  05890000
005900        MOVE AM-PSFMAS-479BFAS OF DCLDZBFASTV TO                  05900000
005910        AM-PS-FORM-AS OF VMBFAS                                   05910000
005920        MOVE NB-FIFMAS-479BFAS OF DCLDZBFASTV TO                  05920000
005930        NB-FI-FORM-AS OF VMBFAS                                   05930000
005940        MOVE AM-FINFMAS-479BFAS OF DCLDZBFASTV TO                 05940000
005950        AM-FIN-FORM-AS OF VMBFAS                                  05950000
005960        MOVE CO-RIFMAS-479BFAS OF DCLDZBFASTV TO                  05960000
005970        CO-RI-FORM-AS OF VMBFAS                                   05970000
005980        MOVE NR-IDRFMAS-479BFAS OF DCLDZBFASTV TO                 05980000
005990        NR-IDR-FORM-AS OF VMBFAS                                  05990000
006000        MOVE DA-UERFMAS-479BFAS OF DCLDZBFASTV TO DA-DD-MM-CCYY   06000000
006010        EVALUATE TRUE                                             06010000
006020          WHEN DA-DD-MM-CCYY = '01.01.0001'                       06020000
006030               MOVE ZEROES TO DA-CCYYMMDD-R                       06030000
006040          WHEN DA-DD-MM-CCYY = '31.12.9999'                       06040000
006050               MOVE '99999999' TO DA-CCYYMMDD-R                   06050000
006060          WHEN OTHER                                              06060000
006070               MOVE CCYY OF DA-DD-MM-CCYY TO CCYY                 06070000
006080               OF DA-CCYYMMDD-R                                   06080000
006090               MOVE MM OF DA-DD-MM-CCYY TO MM OF DA-CCYYMMDD-R    06090000
006100               MOVE DD OF DA-DD-MM-CCYY TO DD OF DA-CCYYMMDD-R    06100000
006110        END-EVALUATE                                              06110000
006120        MOVE DA-CCYYMMDD-R TO DA-UER-FORM-AS OF VMBFAS            06120000
006130        MOVE AM-FBAFMAS-479BFAS OF DCLDZBFASTV TO                 06130000
006140        AM-FBA-FORM-AS OF VMBFAS                                  06140000
006150        MOVE AM-FBBFMAS-479BFAS OF DCLDZBFASTV TO                 06150000
006160        AM-FBB-FORM-AS OF VMBFAS                                  06160000
006170        MOVE CO-RMFMAS-479BFAS OF DCLDZBFASTV TO                  06170000
006180        CO-RM-FORM-AS OF VMBFAS                                   06180000
006190        MOVE RA-FBFMAS-479BFAS OF DCLDZBFASTV TO                  06190000
006200        RA-FB-FORM-AS OF VMBFAS                                   06200000
006210        MOVE NB-FBFMAS-479BFAS OF DCLDZBFASTV TO                  06210000
006220        NB-FB-FORM-AS OF VMBFAS                                   06220000
006230        MOVE AM-FBNFMAS-479BFAS OF DCLDZBFASTV TO                 06230000
006240        AM-FBN-FORM-AS OF VMBFAS                                  06240000
006250        MOVE RA-TIFMAS-479BFAS OF DCLDZBFASTV TO                  06250000
006260        RA-TI-FORM-AS OF VMBFAS                                   06260000
006270        MOVE AM-CNDFMAS-479BFAS OF DCLDZBFASTV TO                 06270000
006280        AM-CND-FORM-AS OF VMBFAS                                  06280000
006290        MOVE AM-CNDNFAS-479BFAS OF DCLDZBFASTV TO                 06290000
006300        AM-CNDN-FORM-AS OF VMBFAS                                 06300000
006310        MOVE AM-CNSNFAS-479BFAS OF DCLDZBFASTV TO                 06310000
006320        AM-CNSN-FORM-AS OF VMBFAS                                 06320000
006330        MOVE NR-CDFMAS-479BFAS OF DCLDZBFASTV TO                  06330000
006340        NR-CD-FORM-AS OF VMBFAS                                   06340000
006350        MOVE CT-SLFMAS-479BFAS OF DCLDZBFASTV TO                  06350000
006360        CT-SL-FORM-AS OF VMBFAS                                   06360000
006370        MOVE NR-STFMAS-479BFAS OF DCLDZBFASTV TO                  06370000
006380        NR-ST-FORM-AS OF VMBFAS                                   06380000
006390        MOVE CX-TWFMAS-479BFAS OF DCLDZBFASTV TO                  06390000
006400        CX-TW-FORM-AS OF VMBFAS                                   06400000
006410        MOVE NR-DSFMAS-479BFAS OF DCLDZBFASTV TO                  06410000
006420        NR-DS-FORM-AS OF VMBFAS                                   06420000
006430        MOVE NR-IDXFMAS-479BFAS OF DCLDZBFASTV TO                 06430000
006440        NR-IDX-FORM-AS OF VMBFAS                                  06440000
006450        MOVE CO-LAFMAS-479BFAS OF DCLDZBFASTV TO                  06450000
006460        CO-LA-FORM-AS OF VMBFAS                                   06460000
006470        MOVE AM-INTFMAS-479BFAS OF DCLDZBFASTV TO                 06470000
006480        AM-INTER-FORM-AS OF VMBFAS                                06480000
006490        MOVE NB-GRPFMAS-479BFAS OF DCLDZBFASTV TO                 06490000
006500        NB-GROUP-FORM-AS OF VMBFAS                                06500000
006510        MOVE NR-PRGRPFS-479BFAS OF DCLDZBFASTV TO                 06510000
006520        NR-PRGRP-FORM-AS OF VMBFAS                                06520000
006530        MOVE NR-NEGRPFS-479BFAS OF DCLDZBFASTV TO                 06530000
006540        NR-NEGRP-FORM-AS OF VMBFAS                                06540000
006550        MOVE NR-FIGRPFS-479BFAS OF DCLDZBFASTV TO                 06550000
006560        NR-FIGRP-FORM-AS OF VMBFAS                                06560000
006570        MOVE NR-SEGRPFS-479BFAS OF DCLDZBFASTV TO                 06570000
006580        NR-SEGRP-FORM-AS OF VMBFAS                                06580000
006590        MOVE NS-IDCPFS-479BFAS OF DCLDZBFASTV TO                  06590000
006600        NS-IDCP-FORM-AS OF VMBFAS                                 06600000
006610        MOVE AM-CNSSPFS-479BFAS OF DCLDZBFASTV TO                 06610000
006620        AM-CNSSP-FORM-AS OF VMBFAS                                06620000
006630        MOVE RA-CPTOTFS-479BFAS OF DCLDZBFASTV TO                 06630000
006640        RA-CPTOT-FORM-AS OF VMBFAS                                06640000
006650        MOVE CO-CPFMAS-479BFAS OF DCLDZBFASTV TO                  06650000
006660        CO-CP-FORM-AS OF VMBFAS                                   06660000
006670        MOVE CO-PERINFS-479BFAS OF DCLDZBFASTV TO                 06670000
006680        CO-PERIN-FORM-AS OF VMBFAS                                06680000
006690        MOVE NS-IDFMAS-479BFAS OF DCLDZBFASTV TO                  06690000
006700        NS-ID-FORM-AS OF VMBFAS                                   06700000
006710        MOVE CO-DEVFMAS-479BFAS OF DCLDZBFASTV TO                 06710000
006720        CO-DEV-FORM-AS OF VMBFAS                                  06720000
006730        MOVE NB-KRDEVFS-479BFAS OF DCLDZBFASTV TO                 06730000
006740        NB-KRDEV-FORM-AS OF VMBFAS                                06740000
006750        MOVE AM-BSDECFS-479BFAS OF DCLDZBFASTV TO                 06750000
006760        AM-BSDEV-FORM-AS OF VMBFAS                                06760000
006770        MOVE CO-TYPFMAS-479BFAS OF DCLDZBFASTV TO                 06770000
006780        CO-TYP-FORM-AS OF VMBFAS                                  06780000
006790        MOVE CO-SUBTPFS-479BFAS OF DCLDZBFASTV TO                 06790000
006800        CO-SUBTP-FORM-AS OF VMBFAS                                06800000
006810        MOVE CO-CONTFS-479BFAS OF DCLDZBFASTV TO                  06810000
006820        CO-CONT-FORM-AS OF VMBFAS                                 06820000
006830        MOVE CO-TPVGLFS-479BFAS OF DCLDZBFASTV TO                 06830000
006840        CO-TPVGL-FORM-AS OF VMBFAS                                06840000
006850        MOVE AM-VGLFMAS-479BFAS OF DCLDZBFASTV TO                 06850000
006860        AM-VGL-FORM-AS OF VMBFAS                                  06860000
006870        MOVE NR-PRDFMAS-479BFAS OF DCLDZBFASTV TO                 06870000
006880        NR-PROD-FORM-AS OF VMBFAS                                 06880000
006890        MOVE DA-ACTVRFS-479BFAS OF DCLDZBFASTV TO DA-DD-MM-CCYY   06890000
006900        EVALUATE TRUE                                             06900000
006910          WHEN DA-DD-MM-CCYY = '01.01.0001'                       06910000
006920               MOVE ZEROES TO DA-CCYYMMDD-R                       06920000
006930          WHEN DA-DD-MM-CCYY = '31.12.9999'                       06930000
006940               MOVE '99999999' TO DA-CCYYMMDD-R                   06940000
006950          WHEN OTHER                                              06950000
006960               MOVE CCYY OF DA-DD-MM-CCYY TO CCYY                 06960000
006970               OF DA-CCYYMMDD-R                                   06970000
006980               MOVE MM OF DA-DD-MM-CCYY TO MM OF DA-CCYYMMDD-R    06980000
006990               MOVE DD OF DA-DD-MM-CCYY TO DD OF DA-CCYYMMDD-R    06990000
007000        END-EVALUATE                                              07000000
007010        MOVE DA-CCYYMMDD-R TO DA-ACTVR-FORM-AS OF VMBFAS          07010000
007020        MOVE DA-INVTRFS-479BFAS OF DCLDZBFASTV TO DA-DD-MM-CCYY   07020000
007030        EVALUATE TRUE                                             07030000
007040          WHEN DA-DD-MM-CCYY = '01.01.0001'                       07040000
007050               MOVE ZEROES TO DA-CCYYMMDD-R                       07050000
007060          WHEN DA-DD-MM-CCYY = '31.12.9999'                       07060000
007070               MOVE '99999999' TO DA-CCYYMMDD-R                   07070000
007080          WHEN OTHER                                              07080000
007090               MOVE CCYY OF DA-DD-MM-CCYY TO CCYY                 07090000
007100               OF DA-CCYYMMDD-R                                   07100000
007110               MOVE MM OF DA-DD-MM-CCYY TO MM OF DA-CCYYMMDD-R    07110000
007120               MOVE DD OF DA-DD-MM-CCYY TO DD OF DA-CCYYMMDD-R    07120000
007130        END-EVALUATE                                              07130000
007140        MOVE DA-CCYYMMDD-R TO DA-INVTR-FORM-AS OF VMBFAS          07140000
007150        MOVE RA-QZTTIFS-479BFAS OF DCLDZBFASTV TO                 07150000
007160        RA-QZTTI-FORM-AS OF VMBFAS                                07160000
007170        MOVE RA-DGTTIFS-479BFAS OF DCLDZBFASTV TO                 07170000
007180        RA-DGTTI-FORM-AS OF VMBFAS                                07180000
007190        MOVE NB-DGTTIFS-479BFAS OF DCLDZBFASTV TO                 07190000
007200        NB-DGTTI-FORM-AS OF VMBFAS                                07200000
007210        MOVE AM-DGTTIFS-479BFAS OF DCLDZBFASTV TO                 07210000
007220        AM-DGTTI-FORM-AS OF VMBFAS                                07220000
007230        MOVE ST-DGTTIFS-479BFAS OF DCLDZBFASTV TO                 07230000
007240        ST-DGTTI-FORM-AS OF VMBFAS                                07240000
007250        MOVE ST-PRRWFS-479BFAS OF DCLDZBFASTV TO                  07250000
007260        ST-PRRW-FORM-AS OF VMBFAS                                 07260000
007270        MOVE RA-GIFTFS-479BFAS OF DCLDZBFASTV TO                  07270000
007280        RA-GIFT-FORM-AS OF VMBFAS                                 07280000
007290        MOVE AM-GIFTFS-479BFAS OF DCLDZBFASTV TO                  07290000
007300        AM-GIFT-FORM-AS OF VMBFAS                                 07300000
007310        MOVE ST-VOORHFS-479BFAS OF DCLDZBFASTV TO                 07310000
007320        ST-VOORH-FORM-AS OF VMBFAS                                07320000
007330        MOVE DA-CPTAFS-479BFAS OF DCLDZBFASTV TO DA-DD-MM-CCYY    07330000
007340        EVALUATE TRUE                                             07340000
007350          WHEN DA-DD-MM-CCYY = '01.01.0001'                       07350000
007360               MOVE ZEROES TO DA-CCYYMMDD-R                       07360000
007370          WHEN DA-DD-MM-CCYY = '31.12.9999'                       07370000
007380               MOVE '99999999' TO DA-CCYYMMDD-R                   07380000
007390          WHEN OTHER                                              07390000
007400               MOVE CCYY OF DA-DD-MM-CCYY TO CCYY                 07400000
007410               OF DA-CCYYMMDD-R                                   07410000
007420               MOVE MM OF DA-DD-MM-CCYY TO MM OF DA-CCYYMMDD-R    07420000
007430               MOVE DD OF DA-DD-MM-CCYY TO DD OF DA-CCYYMMDD-R    07430000
007440        END-EVALUATE                                              07440000
007450        MOVE DA-CCYYMMDD-R TO DA-CPTA-FORM-AS OF VMBFAS           07450000
007460        MOVE CO-EXTOBFS-479BFAS OF DCLDZBFASTV TO                 07460000
007470        CO-EXTOB-FORM-AS OF VMBFAS                                07470000
007480        MOVE CO-PLTOBFS-479BFAS OF DCLDZBFASTV TO                 07480000
007490        CO-PLTOB-FORM-AS OF VMBFAS                                07490000
007500        MOVE RA-TOBFS-479BFAS OF DCLDZBFASTV TO                   07500000
007510        RA-TOB-FORM-AS OF VMBFAS                                  07510000
007520        MOVE AM-TOBFS-479BFAS OF DCLDZBFASTV TO                   07520000
007530        AM-TOB-FORM-AS OF VMBFAS                                  07530000
007540        MOVE RA-TARPHFS-479BFAS OF DCLDZBFASTV TO                 07540000
007550        RA-TARPH-FORM-AS OF VMBFAS                                07550000
007560        MOVE AM-TARPH-479BFAS OF DCLDZBFASTV TO                   07560000
007570        AM-TARPH-FORM-AS OF VMBFAS                                07570000
007580        MOVE AM-BASEFS-479BFAS OF DCLDZBFASTV TO                  07580000
007590        AM-BASE-FORM-AS OF VMBFAS                                 07590000
007600        MOVE AM-FLKFS-479BFAS OF DCLDZBFASTV TO                   07600000
007610        AM-FLK-FORM-AS OF VMBFAS                                  07610000
007620        MOVE NR-ISFMAS-479BFAS OF DCLDZBFASTV                     07620000
007630        TO W-NR-IS-FORM-AS                                        07630000
007640        MOVE W-NR-ID-ISSUE TO F-NR-IS                             07640000
007650        MOVE NR-STFMAS-479BFAS OF DCLDZBFASTV                     07650000
007660        TO F-NR-ST                                                07660000
007670        WRITE FORM-REC FROM REC-FORM                              07670000
007680     END-IF.                                                      07680000
007690*                                                                 07690000
007700*DB2: Expanded LRF NEXT VMBTL03-R01 WHERE SWEEP-VMBFAS -> VMBFAS  07700000
007710*  WITHIN AR-VMBFRM1.                                             07710000
007720*DB2: Converted OBTAIN NEXT VMBFAS WITHIN AR-VMBFRM1.             07720000
007730     PERFORM 720-FETCH-DZBFASC1.                                  07730000
007740*                                                                 07740000
007750 BEHANDELING-EXIT.                                                07750000
007760*                                                                 07760000
007770     EXIT.                                                        07770000
007780*                                                                 07780000
007790*                                                                 07790000
007800 EINDE-PROGRAMMA.                                                 07800000
007810*----------------                                                 07810000
007820*DB2: COMMIT removed; retrieval program is read-only.             07820000
007830     CLOSE FORM.                                                  07830000
007840*                                                                 07840000
007850 EINDE-PROGRAMMA-EXIT.                                            07850000
007860*                                                                 07860000
007870     EXIT.                                                        07870000
007880/                                                                 07880000
007890                                                                  07890000
007900*DB2 GENERATED CURSOR OPEN FETCH CLOSE PARAGRAPHS              *  07900000
007910                                                                  07910000
007920 710-OPEN-DZBFASC1.                                               07920000
007930D    DISPLAY '710-OPEN-DZBFASC1.'                                 07930000
007940     MOVE 710    TO SQL-LOCATION                                  07940000
007950                                                                  07950000
007960     EXEC SQL                                                     07960000
007970       OPEN DZBFASC1                                              07970000
007980     END-EXEC                                                     07980000
007990                                                                  07990000
008000     EVALUATE SQLCODE                                             08000000
008010       WHEN ZERO                                                  08010000
008020            SET DZBFASC1-NOT-EOC TO TRUE                          08020000
008030       WHEN OTHER                                                 08030000
008040            MOVE 710    TO SQL-LOCATION                           08040000
008050            DISPLAY 'ERROR WHILE OPENING CURSOR DZBFASC1'         08050000
008060            PERFORM SQLERROR                                      08060000
008070     END-EVALUATE                                                 08070000
008080     .                                                            08080000
008090                                                                  08090000
008100 720-FETCH-DZBFASC1.                                              08100000
008110D    DISPLAY '720-FETCH-DZBFASC1.'                                08110000
008120     SET DZBFASC1-NOT-EOC TO TRUE                                 08120000
008130     MOVE 720    TO SQL-LOCATION                                  08130000
008140                                                                  08140000
008150     EXEC SQL                                                     08150000
008160       FETCH DZBFASC1                                             08160000
008170       INTO :DCLDZBFASTV.DA-CPTAFS-479BFAS                        08170000
008180       , :DCLDZBFASTV.DA-CRFMAS-479BFAS                           08180000
008190       , :DCLDZBFASTV.NR-ISFMAS-479BFAS                           08190000
008200       , :DCLDZBFASTV.NR-STFMAS-479BFAS                           08200000
008210       , :DCLDZBFASTV.CT-RKTGDSV-479BFAS                          08210000
008220       , :DCLDZBFASTV.NR-CIOFMAS-479BFAS                          08220000
008230       , :DCLDZBFASTV.NR-IDFMAS-479BFAS                           08230000
008240       , :DCLDZBFASTV.CT-OPD-479BFAS                              08240000
008250       , :DCLDZBFASTV.CT-OPG-479BFAS                              08250000
008260       , :DCLDZBFASTV.NR-CIWFMAS-479BFAS                          08260000
008270       , :DCLDZBFASTV.DA-VAFMAS-479BFAS                           08270000
008280       , :DCLDZBFASTV.CO-VMFMAS-479BFAS                           08280000
008290       , :DCLDZBFASTV.RA-RTFMAS-479BFAS                           08290000
008300       , :DCLDZBFASTV.RA-CPFMAS-479BFAS                           08300000
008310       , :DCLDZBFASTV.RA-BASFMAS-479BFAS                          08310000
008320       , :DCLDZBFASTV.DA-UBFMAS-479BFAS                           08320000
008330       , :DCLDZBFASTV.DA-UEFMAS-479BFAS                           08330000
008340       , :DCLDZBFASTV.DU-STFMAS-479BFAS                           08340000
008350       , :DCLDZBFASTV.RA-PSFMAS-479BFAS                           08350000
008360       , :DCLDZBFASTV.RA-PRFMAS-479BFAS                           08360000
008370       , :DCLDZBFASTV.AM-CNSFMAS-479BFAS                          08370000
008380       , :DCLDZBFASTV.AM-PSFMAS-479BFAS                           08380000
008390       , :DCLDZBFASTV.NB-FIFMAS-479BFAS                           08390000
008400       , :DCLDZBFASTV.AM-FINFMAS-479BFAS                          08400000
008410       , :DCLDZBFASTV.CO-RIFMAS-479BFAS                           08410000
008420       , :DCLDZBFASTV.NR-IDRFMAS-479BFAS                          08420000
008430       , :DCLDZBFASTV.DA-UERFMAS-479BFAS                          08430000
008440       , :DCLDZBFASTV.AM-FBAFMAS-479BFAS                          08440000
008450       , :DCLDZBFASTV.AM-FBBFMAS-479BFAS                          08450000
008460       , :DCLDZBFASTV.CO-RMFMAS-479BFAS                           08460000
008470       , :DCLDZBFASTV.RA-FBFMAS-479BFAS                           08470000
008480       , :DCLDZBFASTV.NB-FBFMAS-479BFAS                           08480000
008490       , :DCLDZBFASTV.AM-FBNFMAS-479BFAS                          08490000
008500       , :DCLDZBFASTV.RA-TIFMAS-479BFAS                           08500000
008510       , :DCLDZBFASTV.AM-CNDFMAS-479BFAS                          08510000
008520       , :DCLDZBFASTV.AM-CNDNFAS-479BFAS                          08520000
008530       , :DCLDZBFASTV.AM-CNSNFAS-479BFAS                          08530000
008540       , :DCLDZBFASTV.NR-CDFMAS-479BFAS                           08540000
008550       , :DCLDZBFASTV.CT-SLFMAS-479BFAS                           08550000
008560       , :DCLDZBFASTV.CX-TWFMAS-479BFAS                           08560000
008570       , :DCLDZBFASTV.NR-DSFMAS-479BFAS                           08570000
008580       , :DCLDZBFASTV.NR-IDXFMAS-479BFAS                          08580000
008590       , :DCLDZBFASTV.CO-LAFMAS-479BFAS                           08590000
008600       , :DCLDZBFASTV.AM-INTFMAS-479BFAS                          08600000
008610       , :DCLDZBFASTV.NB-GRPFMAS-479BFAS                          08610000
008620       , :DCLDZBFASTV.NR-PRGRPFS-479BFAS                          08620000
008630       , :DCLDZBFASTV.NR-NEGRPFS-479BFAS                          08630000
008640       , :DCLDZBFASTV.NR-FIGRPFS-479BFAS                          08640000
008650       , :DCLDZBFASTV.NR-SEGRPFS-479BFAS                          08650000
008660       , :DCLDZBFASTV.NS-IDCPFS-479BFAS                           08660000
008670       , :DCLDZBFASTV.AM-CNSSPFS-479BFAS                          08670000
008680       , :DCLDZBFASTV.RA-CPTOTFS-479BFAS                          08680000
008690       , :DCLDZBFASTV.CO-CPFMAS-479BFAS                           08690000
008700       , :DCLDZBFASTV.CO-PERINFS-479BFAS                          08700000
008710       , :DCLDZBFASTV.NS-IDFMAS-479BFAS                           08710000
008720       , :DCLDZBFASTV.CO-DEVFMAS-479BFAS                          08720000
008730       , :DCLDZBFASTV.NB-KRDEVFS-479BFAS                          08730000
008740       , :DCLDZBFASTV.AM-BSDECFS-479BFAS                          08740000
008750       , :DCLDZBFASTV.CO-TYPFMAS-479BFAS                          08750000
008760       , :DCLDZBFASTV.CO-SUBTPFS-479BFAS                          08760000
008770       , :DCLDZBFASTV.CO-CONTFS-479BFAS                           08770000
008780       , :DCLDZBFASTV.CO-TPVGLFS-479BFAS                          08780000
008790       , :DCLDZBFASTV.AM-VGLFMAS-479BFAS                          08790000
008800       , :DCLDZBFASTV.NR-PRDFMAS-479BFAS                          08800000
008810       , :DCLDZBFASTV.DA-ACTVRFS-479BFAS                          08810000
008820       , :DCLDZBFASTV.DA-INVTRFS-479BFAS                          08820000
008830       , :DCLDZBFASTV.RA-QZTTIFS-479BFAS                          08830000
008840       , :DCLDZBFASTV.RA-DGTTIFS-479BFAS                          08840000
008850       , :DCLDZBFASTV.NB-DGTTIFS-479BFAS                          08850000
008860       , :DCLDZBFASTV.AM-DGTTIFS-479BFAS                          08860000
008870       , :DCLDZBFASTV.ST-DGTTIFS-479BFAS                          08870000
008880       , :DCLDZBFASTV.ST-PRRWFS-479BFAS                           08880000
008890       , :DCLDZBFASTV.RA-GIFTFS-479BFAS                           08890000
008900       , :DCLDZBFASTV.AM-GIFTFS-479BFAS                           08900000
008910       , :DCLDZBFASTV.ST-VOORHFS-479BFAS                          08910000
008920       , :DCLDZBFASTV.CO-EXTOBFS-479BFAS                          08920000
008930       , :DCLDZBFASTV.CO-PLTOBFS-479BFAS                          08930000
008940       , :DCLDZBFASTV.RA-TOBFS-479BFAS                            08940000
008950       , :DCLDZBFASTV.AM-TOBFS-479BFAS                            08950000
008960       , :DCLDZBFASTV.RA-TARPHFS-479BFAS                          08960000
008970       , :DCLDZBFASTV.AM-TARPH-479BFAS                            08970000
008980       , :DCLDZBFASTV.AM-BASEFS-479BFAS                           08980000
008990       , :DCLDZBFASTV.AM-FLKFS-479BFAS                            08990000
009000       , :DCLDZBFASTV.NR-CIOFMAS-479SIAS                          09000000
009010       , :DCLDZBFASTV.NR-IDFMAS-479SIAS                           09010000
009020       , :DCLDZBFASTV.NR-ID-479BFAS                               09020000
009030     END-EXEC                                                     09030000
009040                                                                  09040000
009050     EVALUATE SQLCODE                                             09050000
009060       WHEN ZERO                                                  09060000
009070            ADD 1 TO WS-NB-BFAS-COUNT                             09070000
009080            CONTINUE                                              09080000
009090       WHEN 100                                                   09090000
009100            SET DZBFASC1-EOC TO TRUE                              09100000
009110       WHEN OTHER                                                 09110000
009120            MOVE 720    TO SQL-LOCATION                           09120000
009130            DISPLAY 'ERROR WHILE FETCHING CURSOR DZBFASC1'        09130000
009140            DISPLAY 'DA-CPTAFS-479BFAS  : ' DA-CPTAFS-479BFAS     09140000
009150            OF DCLDZBFASTV                                        09150000
009160            DISPLAY 'DA-CRFMAS-479BFAS  : ' DA-CRFMAS-479BFAS     09160000
009170            OF DCLDZBFASTV                                        09170000
009180            DISPLAY 'NR-ISFMAS-479BFAS  : ' NR-ISFMAS-479BFAS     09180000
009190            OF DCLDZBFASTV                                        09190000
009200            DISPLAY 'NR-STFMAS-479BFAS  : ' NR-STFMAS-479BFAS     09200000
009210            OF DCLDZBFASTV                                        09210000
009220            DISPLAY 'CT-RKTGDSV-479BFAS : ' CT-RKTGDSV-479BFAS    09220000
009230            OF DCLDZBFASTV                                        09230000
009240            PERFORM SQLERROR                                      09240000
009250     END-EVALUATE                                                 09250000
009260     .                                                            09260000
009270                                                                  09270000
009280 730-CLOSE-DZBFASC1.                                              09280000
009290D    DISPLAY '730-CLOSE-DZBFASC1.'                                09290000
009300     MOVE 730    TO SQL-LOCATION                                  09300000
009310                                                                  09310000
009320     EXEC SQL                                                     09320000
009330       CLOSE DZBFASC1                                             09330000
009340     END-EXEC                                                     09340000
009350                                                                  09350000
009360     EVALUATE SQLCODE                                             09360000
009370       WHEN ZERO                                                  09370000
009380            CONTINUE                                              09380000
009390       WHEN OTHER                                                 09390000
009400            MOVE 730    TO SQL-LOCATION                           09400000
009410            DISPLAY 'ERROR WHILE CLOSING CURSOR DZBFASC1'         09410000
009420            PERFORM SQLERROR                                      09420000
009430     END-EVALUATE                                                 09430000
009440     .                                                            09440000
009450                                                                  09450000
009460 600-GET-TIMESTAMP.                                               09460000
009470     MOVE FUNCTION CURRENT-DATE            TO TS-SYSTEM.          09470000
009480     MOVE CC OF TS-SYSTEM             TO CC OF TS-TIMESTAMP       09480000
009490     MOVE YY OF TS-SYSTEM             TO YY OF TS-TIMESTAMP       09490000
009500     MOVE MM OF TS-SYSTEM             TO MM OF TS-TIMESTAMP       09500000
009510     MOVE DD OF TS-SYSTEM             TO DD OF TS-TIMESTAMP       09510000
009520     MOVE HH OF TS-SYSTEM             TO HH OF TS-TIMESTAMP       09520000
009530     MOVE MI OF TS-SYSTEM             TO MI OF TS-TIMESTAMP       09530000
009540     MOVE SS OF TS-SYSTEM             TO SS OF TS-TIMESTAMP       09540000
009550     MOVE TT OF TS-SYSTEM             TO TT OF TS-TIMESTAMP       09550000
009560     DISPLAY 'TIMESTAMP: ' TS-TIMESTAMP                           09560000
009570     .                                                            09570000
009580                                                                  09580000
009590*SQLERROR ROUTINE.                                                09590000
009600     EXEC SQL                                                     09600000
009610       INCLUDE SQLERROR                                           09610000
009620     END-EXEC.                                                    09620000
