000010 CBL ARITH(EXTEND)                                                00010000
000020 IDENTIFICATION DIVISION.                                         00020000
000030*========================                                         00030000
000040 PROGRAM-ID. VMDZ7200.                                            00040000
000050 AUTHOR.       Veerapandian.                                      00050000
000060                                                                  00060000
000070******************************************************************00070000
000080*                                                                 00080000
000090*    ARCHIVAGE :  EXTRACT DES FORMULAIRES A ARCHIVER              00090000
000100*    =========    (SOUSCRIPTIONS ET ANNULATIONS SOUSCRIPTIONS)    00100000
000110*                                                                 00110000
000120* WULTEPUTTE KRISTINE : (10/7/91) :                               00120000
000130*                                                                 00130000
000140* TOEVOEGEN VAN NIEUWE PLAGES VOOR BCI1                           00140000
000150*                                                                 00150000
000160* DE SCHEPPER KOEN    : (18/12/92) :                              00160000
000170*                                                                 00170000
000180* AANPASSING VOOR SLIK : UITBREIDING FORM 270 -> 390              00180000
000190*                                                                 00190000
000200* CLEMENT J. (06/93) : TOEVOEGEN PLAGES                           00200000
000210*                                                                 00210000
000220* DE SCHEPPER KOEN     (04/02/94) :                               00220000
000230*    PROGRAMMA VOLLEDIG HERSCHREVEN : GEEN SELECTIE OP            00230000
000240*    WAARDECODE MEER.                                             00240000
000250*                                                                 00250000
000260* POMPONIO S (03/97)                                              00260000
000270*    AANPASSING EURO2000 : PARMDATE EN 8 POSITIONS                00270000
000280*                          RECORD VMBFAS 388 -> 432 BYTES         00280000
000290*                                                                 00290000
000300* J-M BOOGAERTS 2005/02                                           00300000
000310*    INTÉGRATION ARCHIVAGE IUNS P8                                00310000
000320*                                                                 00320000
000330******************************************************************00330000
000340                                                                  00340000
000350 ENVIRONMENT DIVISION.                                            00350000
000360*=====================                                            00360000
000370 CONFIGURATION SECTION.                                           00370000
000380*----------------------                                           00380000
000390 SPECIAL-NAMES.                                                   00390000
000400     DECIMAL-POINT IS COMMA.                                      00400000
000410*                                                                 00410000
000420 INPUT-OUTPUT SECTION.                                            00420000
000430*---------------------                                            00430000
000440 FILE-CONTROL.                                                    00440000
000450     SELECT DAARCH   ASSIGN TO UT-S-DD005.                        00450000
000460     SELECT FORM     ASSIGN TO UT-S-DD010.                        00460000
000470*                                                                 00470000
000480*---------------------                                            00480000
000490/                                                                 00490000
000500 DATA DIVISION.                                                   00500000
000510*==============                                                   00510000
000520 FILE SECTION.                                                    00520000
000530*-------------                                                    00530000
000540*    ----- DATE ARCHIVAGE -----                                   00540000
000550*                                                                 00550000
000560 FD  DAARCH     RECORDING F                                       00560000
000570                RECORD CONTAINS 20                                00570000
000580                BLOCK CONTAINS 0                                  00580000
000590                LABEL RECORD STANDARD.                            00590000
000600 01  DAARCH-REC                PIC X(20).                         00600000
000610*                                                                 00610000
000620*    ----- GESELECTEERDE FORMULIEREN -----                        00620000
000630*                                                                 00630000
000640 FD  FORM       RECORDING F                                       00640000
000650                RECORD CONTAINS 530                               00650000
000660                BLOCK CONTAINS 0                                  00660000
000670                LABEL RECORD STANDARD.                            00670000
000680 01  FORM-REC                  PIC X(530).                        00680000
000690/                                                                 00690000
000700*---------------                                                  00700000
000710*                                                                 00710000
000720 WORKING-STORAGE SECTION.                                         00720000
000730*------------------------                                         00730000
000740*                                                                 00740000
000750 77  USERABEN                  PIC X(8)   VALUE 'USERABEN'.       00750000
000760 77  WS-TELLER                 PIC S9(11) VALUE ZERO.             00760000
000770*                                                                 00770000
000780 01  W-NR-IS-FORM-AS           PIC 9(9).                          00780000
000790 01  FILLER REDEFINES W-NR-IS-FORM-AS.                            00790000
000800     05  W-NR-ID-ISSUE         PIC 9(7).                          00800000
000810     05  W-NR-CD-ISSUE         PIC 9(2).                          00810000
000820*                                                                 00820000
000830 01  REC-FORM.                                                    00830000
000840     05  F-FORM.                                                  00840000
000850*DB2 MATERIALISED IDMS RECORD VMBFAS                              00850000
000860       06  VMBFAS.                                                00860000
000870         07  KY-VMBFAS.                                           00870000
000880           08  NR-RK-GOOD-V02.                                    00880000
000890             09  CT-RK-TGDSERV.                                   00890000
000900               10  CT-RK-TGDSV             PIC X(4).              00900000
000910               10  CT-RK-TGOOD    REDEFINES CT-RK-TGDSV           00910000
000920                   PIC 9(4) VALUE ZEROES.                         00920000
000930             09  GR-ID-GOOD-V02.                                  00930000
000940               10  NR-CIO-FORM-AS          PIC 9(8) VALUE ZEROES. 00940000
000950               10  DA-CR-FORM-AS           PIC 9(8) VALUE ZEROES. 00950000
000960               10  NR-ID-FORM-AS           PIC 9(6) VALUE ZEROES. 00960000
000970               10  CT-OP-FORM-AS.                                 00970000
000980                 11  CT-OPD-FORM-AS        PIC S9(3) VALUE ZEROES.00980000
000990                 11  CT-OPG-FORM-AS         PIC 9(3) VALUE ZEROES.00990000
001000               10  FILLER                  PIC X(2).              01000000
001010         07  AT-FORM-AS.                                          01010000
001020           08  NR-CIW-FORM-AS          PIC X(8).                  01020000
001030           08  DA-VA-FORM-AS.                                     01030000
001040             09  DA-VA-FORM-AS-Y         PIC 9(4) VALUE ZEROES.   01040000
001050             09  DA-VA-FORM-AS-M         PIC 9(2) VALUE ZEROES.   01050000
001060             09  DA-VA-FORM-AS-D         PIC 9(2) VALUE ZEROES.   01060000
001070           08  CO-VM-FORM-AS           PIC X(1).                  01070000
001080           08  NR-IS-FORM-AS           PIC 9(9) VALUE ZEROES.     01080000
001090           08  RA-RT-FORM-AS          PIC S9(3)V9(3) VALUE ZEROES.01090000
001100           08  RA-CP-FORM-AS          PIC S9(3)V9(3) VALUE ZEROES.01100000
001110           08  RA-BASE-FORM-AS        PIC S9(3)V9(3) VALUE ZEROES.01110000
001120           08  DA-UB-FORM-AS.                                     01120000
001130             09  DA-UB-FORM-AS-Y         PIC 9(4) VALUE ZEROES.   01130000
001140             09  DA-UB-FORM-AS-M         PIC 9(2) VALUE ZEROES.   01140000
001150             09  DA-UB-FORM-AS-D         PIC 9(2) VALUE ZEROES.   01150000
001160           08  DA-UE-FORM-AS.                                     01160000
001170             09  DA-UE-FORM-AS-Y         PIC 9(4) VALUE ZEROES.   01170000
001180             09  DA-UE-FORM-AS-M         PIC 9(2) VALUE ZEROES.   01180000
001190             09  DA-UE-FORM-AS-D         PIC 9(2) VALUE ZEROES.   01190000
001200           08  DU-ST-FORM-AS           PIC 9(3) VALUE ZEROES.     01200000
001210           08  RA-PS-FORM-AS          PIC S9(3)V9(3) VALUE ZEROES.01210000
001220           08  RA-PR-FORM-AS          PIC S9(3)V9(3) VALUE ZEROES.01220000
001230           08  AM-CNS-FORM-AS          PIC S9(13)V99 VALUE ZEROES.01230000
001240           08  AM-PS-FORM-AS           PIC S9(13)V99 VALUE ZEROES.01240000
001250           08  NB-FI-FORM-AS           PIC 9(3) VALUE ZEROES.     01250000
001260           08  AM-FIN-FORM-AS          PIC S9(13)V99 VALUE ZEROES.01260000
001270           08  CO-RI-FORM-AS           PIC X(1).                  01270000
001280           08  NR-IDR-FORM-AS          PIC 9(6) VALUE ZEROES.     01280000
001290           08  DA-UER-FORM-AS.                                    01290000
001300             09  DA-UER-FORM-AS-Y        PIC 9(4) VALUE ZEROES.   01300000
001310             09  DA-UER-FORM-AS-M        PIC 9(2) VALUE ZEROES.   01310000
001320             09  DA-UER-FORM-AS-D        PIC 9(2) VALUE ZEROES.   01320000
001330           08  AM-FBA-FORM-AS          PIC S9(13)V99 VALUE ZEROES.01330000
001340           08  AM-FBB-FORM-AS          PIC S9(13)V99 VALUE ZEROES.01340000
001350           08  CO-RM-FORM-AS           PIC X(1).                  01350000
001360           08  RA-FB-FORM-AS          PIC S9(3)V9(3) VALUE ZEROES.01360000
001370           08  NB-FB-FORM-AS           PIC 9(2) VALUE ZEROES.     01370000
001380           08  AM-FBN-FORM-AS          PIC S9(13)V99 VALUE ZEROES.01380000
001390           08  RA-TI-FORM-AS           PIC 9(2)V9(2) VALUE ZEROES.01390000
001400           08  AM-CND-FORM-AS          PIC S9(13)V99 VALUE ZEROES.01400000
001410           08  AM-CNDN-FORM-AS         PIC S9(13)V99 VALUE ZEROES.01410000
001420           08  AM-CNSN-FORM-AS         PIC S9(13)V99 VALUE ZEROES.01420000
001430           08  NR-CD-FORM-AS           PIC 9(4) VALUE ZEROES.     01430000
001440           08  CT-SL-FORM-AS           PIC X(1).                  01440000
001450           08  NR-ST-FORM-AS           PIC 9(13) VALUE ZEROES.    01450000
001460           08  CX-TW-FORM-AS           PIC X(1).                  01460000
001470           08  NR-DS-FORM-AS           PIC 9(12) VALUE ZEROES.    01470000
001480           08  NR-IDX-FORM-AS          PIC 9(6) VALUE ZEROES.     01480000
001490           08  CO-LA-FORM-AS           PIC X(1).                  01490000
001500           08  AM-INTER-FORM-AS        PIC S9(13)V99 VALUE ZEROES.01500000
001510           08  NB-GROUP-FORM-AS        PIC 9(3) VALUE ZEROES.     01510000
001520           08  NR-PRGRP-FORM-AS        PIC 9(6) VALUE ZEROES.     01520000
001530           08  NR-NEGRP-FORM-AS        PIC 9(6) VALUE ZEROES.     01530000
001540           08  NR-FIGRP-FORM-AS        PIC 9(6) VALUE ZEROES.     01540000
001550           08  NR-SEGRP-FORM-AS        PIC 9(3) VALUE ZEROES.     01550000
001560         07  NS-IDCP-FORM-AS         PIC 9(3) VALUE ZEROES.       01560000
001570         07  AM-CNSSP-FORM-AS        PIC S9(13)V99 VALUE ZEROES.  01570000
001580         07  RA-CPTOT-FORM-AS        PIC S9(3)V9(3) VALUE ZEROES. 01580000
001590         07  CO-CP-FORM-AS           PIC X.                       01590000
001600         07  CO-PERIN-FORM-AS        PIC X.                       01600000
001610         07  NS-ID-FORM-AS           PIC 9(2) VALUE ZEROES.       01610000
001620         07  CO-DEV-FORM-AS          PIC X(3).                    01620000
001630         07  NB-KRDEV-FORM-AS        PIC S9(6)V9(5) VALUE ZEROES. 01630000
001640         07  AM-BSDEV-FORM-AS        PIC S9(13)V99 VALUE ZEROES.  01640000
001650         07  CO-TYP-FORM-AS          PIC X(3).                    01650000
001660         07  CO-SUBTP-FORM-AS        PIC X(3).                    01660000
001670         07  CO-CONT-FORM-AS         PIC X(3).                    01670000
001680         07  CO-TPVGL-FORM-AS        PIC X(2).                    01680000
001690         07  AM-VGL-FORM-AS          PIC S9(13)V99 VALUE ZEROES.  01690000
001700         07  NR-PROD-FORM-AS         PIC X(4).                    01700000
001710         07  DA-ACTVR-FORM-AS.                                    01710000
001720           08  DY-ACTVR-FORM-AS        PIC 9(4) VALUE ZEROES.     01720000
001730           08  DM-ACTVR-FORM-AS        PIC 9(2) VALUE ZEROES.     01730000
001740           08  DD-ACTVR-FORM-AS        PIC 9(2) VALUE ZEROES.     01740000
001750         07  DA-INVTR-FORM-AS.                                    01750000
001760           08  DY-INVTR-FORM-AS        PIC 9(4) VALUE ZEROES.     01760000
001770           08  DM-INVTR-FORM-AS        PIC 9(2) VALUE ZEROES.     01770000
001780           08  DD-INVTR-FORM-AS        PIC 9(2) VALUE ZEROES.     01780000
001790         07  RA-QZTTI-FORM-AS        PIC S9(3)V999 VALUE ZEROES.  01790000
001800         07  RA-DGTTI-FORM-AS        PIC S9(3)V9(3) VALUE ZEROES. 01800000
001810         07  NB-DGTTI-FORM-AS        PIC 9(2) VALUE ZEROES.       01810000
001820         07  AM-DGTTI-FORM-AS        PIC S9(13)V99 VALUE ZEROES.  01820000
001830         07  ST-DGTTI-FORM-AS        PIC 9(1) VALUE ZEROES.       01830000
001840         07  ST-PRRW-FORM-AS         PIC 9(1) VALUE ZEROES.       01840000
001850         07  RA-GIFT-FORM-AS         PIC S9(3)V9(3) VALUE ZEROES. 01850000
001860         07  AM-GIFT-FORM-AS         PIC S9(13)V99 VALUE ZEROES.  01860000
001870         07  ST-VOORH-FORM-AS        PIC 9(1) VALUE ZEROES.       01870000
001880         07  DA-CPTA-FORM-AS.                                     01880000
001890           08  DY-CPTA-FORM-AS         PIC 9(4) VALUE ZEROES.     01890000
001900           08  DM-CPTA-FORM-AS         PIC 9(2) VALUE ZEROES.     01900000
001910           08  DD-CPTA-FORM-AS         PIC 9(2) VALUE ZEROES.     01910000
001920         07  CO-EXTOB-FORM-AS        PIC X(1).                    01920000
001930         07  CO-PLTOB-FORM-AS        PIC X(1).                    01930000
001940         07  RA-TOB-FORM-AS          PIC S9(3)V9(3) VALUE ZEROES. 01940000
001950         07  AM-TOB-FORM-AS          PIC S9(13)V99 VALUE ZEROES.  01950000
001960         07  RA-TARPH-FORM-AS        PIC S9(3)V9(3) VALUE ZEROES. 01960000
001970         07  AM-TARPH-FORM-AS        PIC S9(13)V99 VALUE ZEROES.  01970000
001980         07  AM-BASE-FORM-AS         PIC S9(13)V99 VALUE ZEROES.  01980000
001990         07  AM-FLK-FORM-AS          PIC S9(3)V9(2) VALUE ZEROES. 01990000
002000         07  FILLER                  PIC X(0014).                 02000000
002010     05  F-SW-ARCH             PIC X.                             02010000
002020     05  F-SW-VMBFGD           PIC X.                             02020000
002030     05  F-TELLER              PIC 9(11) VALUE ZEROES.            02030000
002040     05  F-NR-IS               PIC 9(7).                          02040000
002050     05  F-NR-ST               PIC 9(13).                         02050000
002060*                                                                 02060000
002070 COPY VMDZ270I.                                                   02070000
002080*                                                                 02080000
002090 01  WS-DATUMS.                                                   02090000
002100     02  DATE-YMD.                                                02100000
002110         03  D-YEAR            PIC 9(2).                          02110000
002120         03  D-MONTH           PIC 9(2).                          02120000
002130         03  D-DAY             PIC 9(2).                          02130000
002140     02  DATE-YMD8.                                               02140000
002150         03  D-CENT            PIC 9(2).                          02150000
002160         03  D-YEAR            PIC 9(2).                          02160000
002170         03  D-MONTH           PIC 9(2).                          02170000
002180         03  D-DAY             PIC 9(2).                          02180000
002190     02  DATE-DMY8.                                               02190000
002200         03  D-DAY             PIC 9(2).                          02200000
002210         03  D-MONTH           PIC 9(2).                          02210000
002220         03  D-CENT            PIC 9(2).                          02220000
002230         03  D-YEAR            PIC 9(2).                          02230000
002240*                                                                 02240000
002250/                                                                 02250000
002260*                                                                 02260000
002270*                                                                 02270000
002280*                                                                 02280000
002290*                                                                 02290000
002300*                                                                 02300000
002310*                                                                 02310000
002320/                                                                 02320000
002330                                                                  02330000
002340*DB2 INFRASTRUCTURE - SQLCA, INCLUDES, FLAGS                   *  02340000
002350     EXEC SQL INCLUDE SQLERRWS END-EXEC.                          02350000
002360     EXEC SQL INCLUDE SQLCA END-EXEC.                             02360000
002370     EXEC SQL INCLUDE DZBFASTV END-EXEC.                          02370000
002380                                                                  02380000
002390*DB2 CURSOR END-OF-CURSOR FLAGS                                *  02390000
002400 01  WS-DZBFASC1-FLAG               PIC X.                        02400000
002410     88  DZBFASC1-NOT-EOC           VALUE 'N'.                    02410000
002420     88  DZBFASC1-EOC               VALUE 'Y'.                    02420000
002430                                                                  02430000
002440                                                                  02440000
002450*DB2 CURSOR DECLARATIONS                                       *  02450000
002460     EXEC SQL DECLARE DZBFASC1 CURSOR WITH HOLD FOR               02460000
002470       SELECT DA_CPTAFS_479BFAS                                   02470000
002480            , DA_CRFMAS_479BFAS                                   02480000
002490            , NR_ISFMAS_479BFAS                                   02490000
002500            , NR_STFMAS_479BFAS                                   02500000
002510            , CT_RKTGDSV_479BFAS                                  02510000
002520            , NR_CIOFMAS_479BFAS                                  02520000
002530            , NR_IDFMAS_479BFAS                                   02530000
002540            , CT_OPD_479BFAS                                      02540000
002550            , CT_OPG_479BFAS                                      02550000
002560            , NR_CIWFMAS_479BFAS                                  02560000
002570            , DA_VAFMAS_479BFAS                                   02570000
002580            , CO_VMFMAS_479BFAS                                   02580000
002590            , RA_RTFMAS_479BFAS                                   02590000
002600            , RA_CPFMAS_479BFAS                                   02600000
002610            , RA_BASFMAS_479BFAS                                  02610000
002620            , DA_UBFMAS_479BFAS                                   02620000
002630            , DA_UEFMAS_479BFAS                                   02630000
002640            , DU_STFMAS_479BFAS                                   02640000
002650            , RA_PSFMAS_479BFAS                                   02650000
002660            , RA_PRFMAS_479BFAS                                   02660000
002670            , AM_CNSFMAS_479BFAS                                  02670000
002680            , AM_PSFMAS_479BFAS                                   02680000
002690            , NB_FIFMAS_479BFAS                                   02690000
002700            , AM_FINFMAS_479BFAS                                  02700000
002710            , CO_RIFMAS_479BFAS                                   02710000
002720            , NR_IDRFMAS_479BFAS                                  02720000
002730            , DA_UERFMAS_479BFAS                                  02730000
002740            , AM_FBAFMAS_479BFAS                                  02740000
002750            , AM_FBBFMAS_479BFAS                                  02750000
002760            , CO_RMFMAS_479BFAS                                   02760000
002770            , RA_FBFMAS_479BFAS                                   02770000
002780            , NB_FBFMAS_479BFAS                                   02780000
002790            , AM_FBNFMAS_479BFAS                                  02790000
002800            , RA_TIFMAS_479BFAS                                   02800000
002810            , AM_CNDFMAS_479BFAS                                  02810000
002820            , AM_CNDNFAS_479BFAS                                  02820000
002830            , AM_CNSNFAS_479BFAS                                  02830000
002840            , NR_CDFMAS_479BFAS                                   02840000
002850            , CT_SLFMAS_479BFAS                                   02850000
002860            , CX_TWFMAS_479BFAS                                   02860000
002870            , NR_DSFMAS_479BFAS                                   02870000
002880            , NR_IDXFMAS_479BFAS                                  02880000
002890            , CO_LAFMAS_479BFAS                                   02890000
002900            , AM_INTFMAS_479BFAS                                  02900000
002910            , NB_GRPFMAS_479BFAS                                  02910000
002920            , NR_PRGRPFS_479BFAS                                  02920000
002930            , NR_NEGRPFS_479BFAS                                  02930000
002940            , NR_FIGRPFS_479BFAS                                  02940000
002950            , NR_SEGRPFS_479BFAS                                  02950000
002960            , NS_IDCPFS_479BFAS                                   02960000
002970            , AM_CNSSPFS_479BFAS                                  02970000
002980            , RA_CPTOTFS_479BFAS                                  02980000
002990            , CO_CPFMAS_479BFAS                                   02990000
003000            , CO_PERINFS_479BFAS                                  03000000
003010            , NS_IDFMAS_479BFAS                                   03010000
003020            , CO_DEVFMAS_479BFAS                                  03020000
003030            , NB_KRDEVFS_479BFAS                                  03030000
003040            , AM_BSDECFS_479BFAS                                  03040000
003050            , CO_TYPFMAS_479BFAS                                  03050000
003060            , CO_SUBTPFS_479BFAS                                  03060000
003070            , CO_CONTFS_479BFAS                                   03070000
003080            , CO_TPVGLFS_479BFAS                                  03080000
003090            , AM_VGLFMAS_479BFAS                                  03090000
003100            , NR_PRDFMAS_479BFAS                                  03100000
003110            , DA_ACTVRFS_479BFAS                                  03110000
003120            , DA_INVTRFS_479BFAS                                  03120000
003130            , RA_QZTTIFS_479BFAS                                  03130000
003140            , RA_DGTTIFS_479BFAS                                  03140000
003150            , NB_DGTTIFS_479BFAS                                  03150000
003160            , AM_DGTTIFS_479BFAS                                  03160000
003170            , ST_DGTTIFS_479BFAS                                  03170000
003180            , ST_PRRWFS_479BFAS                                   03180000
003190            , RA_GIFTFS_479BFAS                                   03190000
003200            , AM_GIFTFS_479BFAS                                   03200000
003210            , ST_VOORHFS_479BFAS                                  03210000
003220            , CO_EXTOBFS_479BFAS                                  03220000
003230            , CO_PLTOBFS_479BFAS                                  03230000
003240            , RA_TOBFS_479BFAS                                    03240000
003250            , AM_TOBFS_479BFAS                                    03250000
003260            , RA_TARPHFS_479BFAS                                  03260000
003270            , AM_TARPH_479BFAS                                    03270000
003280            , AM_BASEFS_479BFAS                                   03280000
003290            , AM_FLKFS_479BFAS                                    03290000
003300            , NR_CIOFMAS_479SIAS                                  03300000
003310            , NR_IDFMAS_479SIAS                                   03310000
003320            , NR_ID_479BFAS                                       03320000
003330       FROM DZBFASTV                                              03330000
003340       ORDER BY NR_ID_479BFAS ASC                                 03340000
003350       FOR READ ONLY                                              03350000
003360       QUERYNO 254                                                03360000
003370     END-EXEC.                                                    03370000
003380                                                                  03380000
003390*DB2 DATE CONVERSION WORKING STORAGE                              03390000
003400 01  WS-DATUMVELDEN.                                              03400000
003410     03  DA-CCYYMMDD.                                             03410000
003420         05  CC                    PIC 99       VALUE ZERO.       03420000
003430         05  YY                    PIC 99       VALUE ZERO.       03430000
003440         05  MM                    PIC 99       VALUE ZERO.       03440000
003450         05  DD                    PIC 99       VALUE ZERO.       03450000
003460     03  DA-CCYYMMDD-R REDEFINES DA-CCYYMMDD.                     03460000
003470         05  CCYY                  PIC 9999.                      03470000
003480         05  MM                    PIC 99.                        03480000
003490         05  DD                    PIC 99.                        03490000
003500     03  DA-DD-MM-CCYY.                                           03500000
003510         05  DD                    PIC 9(02).                     03510000
003520         05  TE-MARKER5            PIC X        VALUE '.'.        03520000
003530         05  MM                    PIC 9(02).                     03530000
003540         05  TE-MARKER6            PIC X        VALUE '.'.        03540000
003550         05  CCYY                  PIC 9(04).                     03550000
003560     02  HELP-DA-CPTAFS-479BFAS         PIC 9(8)     VALUE ZEROES.03560000
003570     02  HELP-DA-CRFMAS-479BFAS         PIC 9(8)     VALUE ZEROES.03570000
003580                                                                  03580000
003590                                                                  03590000
003600*DB2 GENERATED WORKING STORAGE                                    03600000
003610 01  WS-DB2-GENERATED.                                            03610000
003620     10  CS-PROGRAM               PIC X(8)    VALUE 'VMDZ7200'.   03620000
003630     10  WS-NB-OUTPUT-COUNT       PIC 9(7)    COMP-3 VALUE ZEROES.03630000
003640     10  WS-NB-BFAS-COUNT         PIC 9(7)    COMP-3 VALUE ZEROES.03640000
003650                                                                  03650000
003660*DB2 GENERATED TIMESTAMP AND AUDIT WORKING STORAGE                03660000
003670 01  WS-TIMESTAMP-FIELDS.                                         03670000
003680     05 TS-SYSTEM.                                                03680000
003690        10  DA-SYS.                                               03690000
003700            15  DA-SYS-CCYY.                                      03700000
003710                20  CC            PIC X(2).                       03710000
003720                20  YY            PIC X(2).                       03720000
003730            15  MM                PIC X(2).                       03730000
003740            15  DD                PIC X(2).                       03740000
003750        10  HR-SYS.                                               03750000
003760            15  HH                PIC X(2).                       03760000
003770            15  MI                PIC X(2).                       03770000
003780            15  SS                PIC X(2).                       03780000
003790            15  TT                PIC X(2).                       03790000
003800     05 TS-TIMESTAMP.                                             03800000
003810        10  CC                    PIC X(2).                       03810000
003820        10  YY                    PIC X(2).                       03820000
003830        10  TE-MARKER1            PIC X             VALUE '-'.    03830000
003840        10  MM                    PIC X(2).                       03840000
003850        10  TE-MARKER2            PIC X             VALUE '-'.    03850000
003860        10  DD                    PIC X(2).                       03860000
003870        10  TE-MARKER3            PIC X             VALUE '-'.    03870000
003880        10  HH                    PIC X(2).                       03880000
003890        10  TE-MARKER4            PIC X             VALUE '.'.    03890000
003900        10  MI                    PIC X(2).                       03900000
003910        10  TE-MARKER5            PIC X             VALUE '.'.    03910000
003920        10  SS                    PIC X(2).                       03920000
003930        10  TE-MARKER6            PIC X             VALUE '.'.    03930000
003940        10  TT                    PIC X(2).                       03940000
003950        10  NNNN                  PIC 9(04)         VALUE 0.      03950000
003960                                                                  03960000
003970 LINKAGE SECTION.                                                 03970000
003980 01  PARAM-ZONEDO.                                                03980000
003990     02  L-PARAM          PIC S9(4)   COMP.                       03990000
004000     02  DATUMLS.                                                 04000000
004010         03  DATE-IND     PIC X.                                  04010000
004020         03  DATE8-LS     PIC 9(8).                               04020000
004030/                                                                 04030000
004040 PROCEDURE DIVISION USING PARAM-ZONEDO.                           04040000
004050*======================================                           04050000
004060     PERFORM 600-GET-TIMESTAMP.                                   04060000
004070     PERFORM BEGIN-PROGRAMMA THRU BEGIN-PROGRAMMA-EXIT.           04070000
004080     PERFORM BEHANDELING THRU BEHANDELING-EXIT                    04080000
004090             UNTIL DZBFASC1-EOC.                                  04090000
004100     PERFORM 730-CLOSE-DZBFASC1.                                  04100000
004110     PERFORM EINDE-PROGRAMMA THRU EINDE-PROGRAMMA-EXIT.           04110000
004120*                                                                 04120000
004130     DISPLAY 'TOTAL BFAS RECORDS   : ' WS-NB-BFAS-COUNT           04130000
004140     DISPLAY 'TOTAL OUTPUT RECORDS : ' WS-NB-OUTPUT-COUNT         04140000
004150                                                                  04150000
004160     GOBACK.                                                      04160000
004170*                                                                 04170000
004180*                                                                 04180000
004190 BEGIN-PROGRAMMA.                                                 04190000
004200*----------------                                                 04200000
004210     IF DATE-IND = '0'                                            04210000
004220        ACCEPT DATE-YMD         FROM DATE                         04220000
004230        MOVE CORR DATE-YMD    TO DATE-DMY8                        04230000
004240        IF D-YEAR OF DATE-YMD > 60                                04240000
004250           MOVE 19            TO D-CENT OF DATE-DMY8              04250000
004260        ELSE                                                      04260000
004270           MOVE 20            TO D-CENT OF DATE-DMY8              04270000
004280        END-IF                                                    04280000
004290     ELSE                                                         04290000
004300        MOVE DATE8-LS         TO DATE-DMY8                        04300000
004310        MOVE CORR DATE-DMY8   TO DATE-YMD                         04310000
004320     END-IF.                                                      04320000
004330     MOVE CORR DATE-DMY8      TO DATE-YMD8.                       04330000
004340                                                                  04340000
004350*                                                                 04350000
004360     MOVE SPACES TO REC-FORM.                                     04360000
004370*                                                                 04370000
004380     OPEN INPUT  DAARCH                                           04380000
004390     OUTPUT FORM.                                                 04390000
004400     READ DAARCH INTO VMDZ270I-REC                                04400000
004410        AT END                                                    04410000
004420        DISPLAY 'VM7BD200: ** DATE ARCHIVAGE NOT OK **'           04420000
004430        CALL USERABEN.                                            04430000
004440        DISPLAY 'DATE ARCH : ' DA-ARCH-YMD.                       04440000
004450        CLOSE DAARCH.                                             04450000
004460*                                                                 04460000
004470        MOVE CS-PROGRAM   TO PROGRAM-NAME.                        04470000
004480*                                                                 04480000
004490*DB2: Expanded LRF FIRST VMBTL03-R01 WHERE SWEEP-VMBFAS -> VMBFAS 04490000
004500*  WITHIN AR-VMBFRM1.                                             04500000
004510        INITIALIZE DCLDZBFASTV                                    04510000
004520        PERFORM 710-OPEN-DZBFASC1.                                04520000
004530        PERFORM 720-FETCH-DZBFASC1.                               04530000
004540*                                                                 04540000
004550 BEGIN-PROGRAMMA-EXIT.                                            04550000
004560*                                                                 04560000
004570     EXIT.                                                        04570000
004580*                                                                 04580000
004590*                                                                 04590000
004600 BEHANDELING.                                                     04600000
004610*------------                                                     04610000
004620     MOVE ZEROES TO DA-CCYYMMDD                                   04620000
004630     MOVE ZEROES TO HELP-DA-CPTAFS-479BFAS                        04630000
004640     MOVE DA-CPTAFS-479BFAS OF DCLDZBFASTV TO DA-DD-MM-CCYY       04640000
004650     EVALUATE TRUE                                                04650000
004660       WHEN DA-DD-MM-CCYY = '01.01.0001'                          04660000
004670            MOVE ZEROES TO DA-CCYYMMDD-R                          04670000
004680       WHEN DA-DD-MM-CCYY = '31.12.9999'                          04680000
004690            MOVE '99999999' TO DA-CCYYMMDD-R                      04690000
004700       WHEN OTHER                                                 04700000
004710            MOVE CCYY OF DA-DD-MM-CCYY TO CCYY OF DA-CCYYMMDD-R   04710000
004720            MOVE MM   OF DA-DD-MM-CCYY TO MM   OF DA-CCYYMMDD-R   04720000
004730            MOVE DD   OF DA-DD-MM-CCYY TO DD   OF DA-CCYYMMDD-R   04730000
004740     END-EVALUATE                                                 04740000
004750     MOVE DA-CCYYMMDD-R TO HELP-DA-CPTAFS-479BFAS                 04750000
004760     MOVE ZEROES TO DA-CCYYMMDD                                   04760000
004770     MOVE ZEROES TO HELP-DA-CRFMAS-479BFAS                        04770000
004780     MOVE DA-CRFMAS-479BFAS OF DCLDZBFASTV TO DA-DD-MM-CCYY       04780000
004790     EVALUATE TRUE                                                04790000
004800       WHEN DA-DD-MM-CCYY = '01.01.0001'                          04800000
004810            MOVE ZEROES TO DA-CCYYMMDD-R                          04810000
004820       WHEN DA-DD-MM-CCYY = '31.12.9999'                          04820000
004830            MOVE '99999999' TO DA-CCYYMMDD-R                      04830000
004840       WHEN OTHER                                                 04840000
004850            MOVE CCYY OF DA-DD-MM-CCYY TO CCYY OF DA-CCYYMMDD-R   04850000
004860            MOVE MM   OF DA-DD-MM-CCYY TO MM   OF DA-CCYYMMDD-R   04860000
004870            MOVE DD   OF DA-DD-MM-CCYY TO DD   OF DA-CCYYMMDD-R   04870000
004880     END-EVALUATE                                                 04880000
004890     MOVE DA-CCYYMMDD-R TO HELP-DA-CRFMAS-479BFAS                 04890000
004900     IF (HELP-DA-CPTAFS-479BFAS < DA-ARCH-YMD  AND                04900000
004910         HELP-DA-CPTAFS-479BFAS NOT = '00000000') OR              04910000
004920        (HELP-DA-CRFMAS-479BFAS < DA-ARCH-YMD AND                 04920000
004930         HELP-DA-CPTAFS-479BFAS = '00000000')                     04930000
004940        PERFORM WRITE-FORM-REC                                    04940000
004950        ADD 1 TO WS-NB-OUTPUT-COUNT                               04950000
004960     END-IF.                                                      04960000
004970*                                                                 04970000
004980*DB2: Expanded LRF NEXT VMBTL03-R01 WHERE SWEEP-VMBFAS -> VMBFAS  04980000
004990*  WITHIN AR-VMBFRM1.                                             04990000
005000     PERFORM 720-FETCH-DZBFASC1.                                  05000000
005010*                                                                 05010000
005020                                                                  05020000
005030/                                                                 05030000
005040 WRITE-FORM-REC.                                                  05040000
005050     ADD 1              TO WS-TELLER                              05050000
005060     MOVE WS-TELLER     TO F-TELLER                               05060000
005070     MOVE CT-RKTGDSV-479BFAS OF DCLDZBFASTV TO                    05070000
005080          CT-RK-TGDSV OF VMBFAS                                   05080000
005090     MOVE NR-CIOFMAS-479BFAS OF DCLDZBFASTV TO                    05090000
005100          NR-CIO-FORM-AS OF VMBFAS                                05100000
005110     MOVE DA-CRFMAS-479BFAS OF DCLDZBFASTV TO DA-DD-MM-CCYY       05110000
005120     EVALUATE TRUE                                                05120000
005130       WHEN DA-DD-MM-CCYY = '01.01.0001'                          05130000
005140            MOVE ZEROES TO DA-CCYYMMDD-R                          05140000
005150       WHEN DA-DD-MM-CCYY = '31.12.9999'                          05150000
005160            MOVE '99999999' TO DA-CCYYMMDD-R                      05160000
005170       WHEN OTHER                                                 05170000
005180            MOVE CCYY OF DA-DD-MM-CCYY TO CCYY OF DA-CCYYMMDD-R   05180000
005190            MOVE MM   OF DA-DD-MM-CCYY TO MM   OF DA-CCYYMMDD-R   05190000
005200            MOVE DD   OF DA-DD-MM-CCYY TO DD   OF DA-CCYYMMDD-R   05200000
005210     END-EVALUATE                                                 05210000
005220     MOVE DA-CCYYMMDD-R TO DA-CR-FORM-AS OF VMBFAS                05220000
005230     MOVE NR-IDFMAS-479BFAS OF DCLDZBFASTV TO                     05230000
005240          NR-ID-FORM-AS OF VMBFAS                                 05240000
005250     MOVE CT-OPD-479BFAS OF DCLDZBFASTV TO                        05250000
005260          CT-OPD-FORM-AS OF VMBFAS                                05260000
005270     MOVE CT-OPG-479BFAS OF DCLDZBFASTV TO                        05270000
005280          CT-OPG-FORM-AS OF VMBFAS                                05280000
005290     MOVE NR-CIWFMAS-479BFAS OF DCLDZBFASTV TO                    05290000
005300          NR-CIW-FORM-AS OF VMBFAS                                05300000
005310     MOVE DA-VAFMAS-479BFAS OF DCLDZBFASTV TO DA-DD-MM-CCYY       05310000
005320     EVALUATE TRUE                                                05320000
005330       WHEN DA-DD-MM-CCYY = '01.01.0001'                          05330000
005340            MOVE ZEROES TO DA-CCYYMMDD-R                          05340000
005350       WHEN DA-DD-MM-CCYY = '31.12.9999'                          05350000
005360            MOVE '99999999' TO DA-CCYYMMDD-R                      05360000
005370       WHEN OTHER                                                 05370000
005380            MOVE CCYY OF DA-DD-MM-CCYY TO CCYY OF DA-CCYYMMDD-R   05380000
005390            MOVE MM   OF DA-DD-MM-CCYY TO MM   OF DA-CCYYMMDD-R   05390000
005400            MOVE DD   OF DA-DD-MM-CCYY TO DD   OF DA-CCYYMMDD-R   05400000
005410     END-EVALUATE                                                 05410000
005420     MOVE DA-CCYYMMDD-R TO DA-VA-FORM-AS OF VMBFAS                05420000
005430     MOVE CO-VMFMAS-479BFAS OF DCLDZBFASTV TO                     05430000
005440          CO-VM-FORM-AS OF VMBFAS                                 05440000
005450     MOVE NR-ISFMAS-479BFAS OF DCLDZBFASTV TO                     05450000
005460          NR-IS-FORM-AS OF VMBFAS                                 05460000
005470     MOVE RA-RTFMAS-479BFAS OF DCLDZBFASTV TO                     05470000
005480          RA-RT-FORM-AS OF VMBFAS                                 05480000
005490     MOVE RA-CPFMAS-479BFAS OF DCLDZBFASTV TO                     05490000
005500          RA-CP-FORM-AS OF VMBFAS                                 05500000
005510     MOVE RA-BASFMAS-479BFAS OF DCLDZBFASTV TO                    05510000
005520          RA-BASE-FORM-AS OF VMBFAS                               05520000
005530     MOVE DA-UBFMAS-479BFAS OF DCLDZBFASTV TO DA-DD-MM-CCYY       05530000
005540     EVALUATE TRUE                                                05540000
005550       WHEN DA-DD-MM-CCYY = '01.01.0001'                          05550000
005560            MOVE ZEROES TO DA-CCYYMMDD-R                          05560000
005570       WHEN DA-DD-MM-CCYY = '31.12.9999'                          05570000
005580            MOVE '99999999' TO DA-CCYYMMDD-R                      05580000
005590       WHEN OTHER                                                 05590000
005600            MOVE CCYY OF DA-DD-MM-CCYY TO CCYY OF DA-CCYYMMDD-R   05600000
005610            MOVE MM   OF DA-DD-MM-CCYY TO MM   OF DA-CCYYMMDD-R   05610000
005620            MOVE DD   OF DA-DD-MM-CCYY TO DD   OF DA-CCYYMMDD-R   05620000
005630     END-EVALUATE                                                 05630000
005640     MOVE DA-CCYYMMDD-R TO DA-UB-FORM-AS OF VMBFAS                05640000
005650     MOVE DA-UEFMAS-479BFAS OF DCLDZBFASTV TO DA-DD-MM-CCYY       05650000
005660     EVALUATE TRUE                                                05660000
005670       WHEN DA-DD-MM-CCYY = '01.01.0001'                          05670000
005680            MOVE ZEROES TO DA-CCYYMMDD-R                          05680000
005690       WHEN DA-DD-MM-CCYY = '31.12.9999'                          05690000
005700            MOVE '99999999' TO DA-CCYYMMDD-R                      05700000
005710       WHEN OTHER                                                 05710000
005720            MOVE CCYY OF DA-DD-MM-CCYY TO CCYY OF DA-CCYYMMDD-R   05720000
005730            MOVE MM   OF DA-DD-MM-CCYY TO MM   OF DA-CCYYMMDD-R   05730000
005740            MOVE DD   OF DA-DD-MM-CCYY TO DD   OF DA-CCYYMMDD-R   05740000
005750     END-EVALUATE                                                 05750000
005760     MOVE DA-CCYYMMDD-R TO DA-UE-FORM-AS OF VMBFAS                05760000
005770     MOVE DU-STFMAS-479BFAS OF DCLDZBFASTV TO                     05770000
005780          DU-ST-FORM-AS OF VMBFAS                                 05780000
005790     MOVE RA-PSFMAS-479BFAS OF DCLDZBFASTV TO                     05790000
005800          RA-PS-FORM-AS OF VMBFAS                                 05800000
005810     MOVE RA-PRFMAS-479BFAS OF DCLDZBFASTV TO                     05810000
005820          RA-PR-FORM-AS OF VMBFAS                                 05820000
005830     MOVE AM-CNSFMAS-479BFAS OF DCLDZBFASTV TO                    05830000
005840          AM-CNS-FORM-AS OF VMBFAS                                05840000
005850     MOVE AM-PSFMAS-479BFAS OF DCLDZBFASTV TO                     05850000
005860          AM-PS-FORM-AS OF VMBFAS                                 05860000
005870     MOVE NB-FIFMAS-479BFAS OF DCLDZBFASTV TO                     05870000
005880          NB-FI-FORM-AS OF VMBFAS                                 05880000
005890     MOVE AM-FINFMAS-479BFAS OF DCLDZBFASTV TO                    05890000
005900          AM-FIN-FORM-AS OF VMBFAS                                05900000
005910     MOVE CO-RIFMAS-479BFAS OF DCLDZBFASTV TO                     05910000
005920          CO-RI-FORM-AS OF VMBFAS                                 05920000
005930     MOVE NR-IDRFMAS-479BFAS OF DCLDZBFASTV TO                    05930000
005940          NR-IDR-FORM-AS OF VMBFAS                                05940000
005950     MOVE DA-UERFMAS-479BFAS OF DCLDZBFASTV TO DA-DD-MM-CCYY      05950000
005960     EVALUATE TRUE                                                05960000
005970       WHEN DA-DD-MM-CCYY = '01.01.0001'                          05970000
005980            MOVE ZEROES TO DA-CCYYMMDD-R                          05980000
005990       WHEN DA-DD-MM-CCYY = '31.12.9999'                          05990000
006000            MOVE '99999999' TO DA-CCYYMMDD-R                      06000000
006010       WHEN OTHER                                                 06010000
006020            MOVE CCYY OF DA-DD-MM-CCYY TO CCYY OF DA-CCYYMMDD-R   06020000
006030            MOVE MM   OF DA-DD-MM-CCYY TO MM   OF DA-CCYYMMDD-R   06030000
006040            MOVE DD   OF DA-DD-MM-CCYY TO DD   OF DA-CCYYMMDD-R   06040000
006050     END-EVALUATE                                                 06050000
006060     MOVE DA-CCYYMMDD-R TO DA-UER-FORM-AS OF VMBFAS               06060000
006070     MOVE AM-FBAFMAS-479BFAS OF DCLDZBFASTV TO                    06070000
006080          AM-FBA-FORM-AS OF VMBFAS                                06080000
006090     MOVE AM-FBBFMAS-479BFAS OF DCLDZBFASTV TO                    06090000
006100          AM-FBB-FORM-AS OF VMBFAS                                06100000
006110     MOVE CO-RMFMAS-479BFAS OF DCLDZBFASTV TO                     06110000
006120          CO-RM-FORM-AS OF VMBFAS                                 06120000
006130     MOVE RA-FBFMAS-479BFAS OF DCLDZBFASTV TO                     06130000
006140          RA-FB-FORM-AS OF VMBFAS                                 06140000
006150     MOVE NB-FBFMAS-479BFAS OF DCLDZBFASTV TO                     06150000
006160          NB-FB-FORM-AS OF VMBFAS                                 06160000
006170     MOVE AM-FBNFMAS-479BFAS OF DCLDZBFASTV TO                    06170000
006180          AM-FBN-FORM-AS OF VMBFAS                                06180000
006190     MOVE RA-TIFMAS-479BFAS OF DCLDZBFASTV TO                     06190000
006200          RA-TI-FORM-AS OF VMBFAS                                 06200000
006210     MOVE AM-CNDFMAS-479BFAS OF DCLDZBFASTV TO                    06210000
006220          AM-CND-FORM-AS OF VMBFAS                                06220000
006230     MOVE AM-CNDNFAS-479BFAS OF DCLDZBFASTV TO                    06230000
006240          AM-CNDN-FORM-AS OF VMBFAS                               06240000
006250     MOVE AM-CNSNFAS-479BFAS OF DCLDZBFASTV TO                    06250000
006260          AM-CNSN-FORM-AS OF VMBFAS                               06260000
006270     MOVE NR-CDFMAS-479BFAS OF DCLDZBFASTV TO                     06270000
006280          NR-CD-FORM-AS OF VMBFAS                                 06280000
006290     MOVE CT-SLFMAS-479BFAS OF DCLDZBFASTV TO                     06290000
006300          CT-SL-FORM-AS OF VMBFAS                                 06300000
006310     MOVE NR-STFMAS-479BFAS OF DCLDZBFASTV TO                     06310000
006320          NR-ST-FORM-AS OF VMBFAS                                 06320000
006330     MOVE CX-TWFMAS-479BFAS OF DCLDZBFASTV TO                     06330000
006340          CX-TW-FORM-AS OF VMBFAS                                 06340000
006350     MOVE NR-DSFMAS-479BFAS OF DCLDZBFASTV TO                     06350000
006360          NR-DS-FORM-AS OF VMBFAS                                 06360000
006370     MOVE NR-IDXFMAS-479BFAS OF DCLDZBFASTV TO                    06370000
006380          NR-IDX-FORM-AS OF VMBFAS                                06380000
006390     MOVE CO-LAFMAS-479BFAS OF DCLDZBFASTV TO                     06390000
006400          CO-LA-FORM-AS OF VMBFAS                                 06400000
006410     MOVE AM-INTFMAS-479BFAS OF DCLDZBFASTV TO                    06410000
006420          AM-INTER-FORM-AS OF VMBFAS                              06420000
006430     MOVE NB-GRPFMAS-479BFAS OF DCLDZBFASTV TO                    06430000
006440          NB-GROUP-FORM-AS OF VMBFAS                              06440000
006450     MOVE NR-PRGRPFS-479BFAS OF DCLDZBFASTV TO                    06450000
006460          NR-PRGRP-FORM-AS OF VMBFAS                              06460000
006470     MOVE NR-NEGRPFS-479BFAS OF DCLDZBFASTV TO                    06470000
006480          NR-NEGRP-FORM-AS OF VMBFAS                              06480000
006490     MOVE NR-FIGRPFS-479BFAS OF DCLDZBFASTV TO                    06490000
006500          NR-FIGRP-FORM-AS OF VMBFAS                              06500000
006510     MOVE NR-SEGRPFS-479BFAS OF DCLDZBFASTV TO                    06510000
006520          NR-SEGRP-FORM-AS OF VMBFAS                              06520000
006530     MOVE NS-IDCPFS-479BFAS OF DCLDZBFASTV TO                     06530000
006540          NS-IDCP-FORM-AS OF VMBFAS                               06540000
006550     MOVE AM-CNSSPFS-479BFAS OF DCLDZBFASTV TO                    06550000
006560          AM-CNSSP-FORM-AS OF VMBFAS                              06560000
006570     MOVE RA-CPTOTFS-479BFAS OF DCLDZBFASTV TO                    06570000
006580          RA-CPTOT-FORM-AS OF VMBFAS                              06580000
006590     MOVE CO-CPFMAS-479BFAS OF DCLDZBFASTV TO                     06590000
006600          CO-CP-FORM-AS OF VMBFAS                                 06600000
006610     MOVE CO-PERINFS-479BFAS OF DCLDZBFASTV TO                    06610000
006620          CO-PERIN-FORM-AS OF VMBFAS                              06620000
006630     MOVE NS-IDFMAS-479BFAS OF DCLDZBFASTV TO                     06630000
006640          NS-ID-FORM-AS OF VMBFAS                                 06640000
006650     MOVE CO-DEVFMAS-479BFAS OF DCLDZBFASTV TO                    06650000
006660          CO-DEV-FORM-AS OF VMBFAS                                06660000
006670     MOVE NB-KRDEVFS-479BFAS OF DCLDZBFASTV TO                    06670000
006680          NB-KRDEV-FORM-AS OF VMBFAS                              06680000
006690     MOVE AM-BSDECFS-479BFAS OF DCLDZBFASTV TO                    06690000
006700          AM-BSDEV-FORM-AS OF VMBFAS                              06700000
006710     MOVE CO-TYPFMAS-479BFAS OF DCLDZBFASTV TO                    06710000
006720          CO-TYP-FORM-AS OF VMBFAS                                06720000
006730     MOVE CO-SUBTPFS-479BFAS OF DCLDZBFASTV TO                    06730000
006740          CO-SUBTP-FORM-AS OF VMBFAS                              06740000
006750     MOVE CO-CONTFS-479BFAS OF DCLDZBFASTV TO                     06750000
006760          CO-CONT-FORM-AS OF VMBFAS                               06760000
006770     MOVE CO-TPVGLFS-479BFAS OF DCLDZBFASTV TO                    06770000
006780          CO-TPVGL-FORM-AS OF VMBFAS                              06780000
006790     MOVE AM-VGLFMAS-479BFAS OF DCLDZBFASTV TO                    06790000
006800          AM-VGL-FORM-AS OF VMBFAS                                06800000
006810     MOVE NR-PRDFMAS-479BFAS OF DCLDZBFASTV TO                    06810000
006820          NR-PROD-FORM-AS OF VMBFAS                               06820000
006830     MOVE DA-ACTVRFS-479BFAS OF DCLDZBFASTV TO DA-DD-MM-CCYY      06830000
006840     EVALUATE TRUE                                                06840000
006850       WHEN DA-DD-MM-CCYY = '01.01.0001'                          06850000
006860            MOVE ZEROES TO DA-CCYYMMDD-R                          06860000
006870       WHEN DA-DD-MM-CCYY = '31.12.9999'                          06870000
006880            MOVE '99999999' TO DA-CCYYMMDD-R                      06880000
006890       WHEN OTHER                                                 06890000
006900            MOVE CCYY OF DA-DD-MM-CCYY TO CCYY OF DA-CCYYMMDD-R   06900000
006910            MOVE MM   OF DA-DD-MM-CCYY TO MM   OF DA-CCYYMMDD-R   06910000
006920            MOVE DD   OF DA-DD-MM-CCYY TO DD   OF DA-CCYYMMDD-R   06920000
006930     END-EVALUATE                                                 06930000
006940     MOVE DA-CCYYMMDD-R TO DA-ACTVR-FORM-AS OF VMBFAS             06940000
006950     MOVE DA-INVTRFS-479BFAS OF DCLDZBFASTV TO DA-DD-MM-CCYY      06950000
006960     EVALUATE TRUE                                                06960000
006970       WHEN DA-DD-MM-CCYY = '01.01.0001'                          06970000
006980            MOVE ZEROES TO DA-CCYYMMDD-R                          06980000
006990       WHEN DA-DD-MM-CCYY = '31.12.9999'                          06990000
007000            MOVE '99999999' TO DA-CCYYMMDD-R                      07000000
007010       WHEN OTHER                                                 07010000
007020            MOVE CCYY OF DA-DD-MM-CCYY TO CCYY OF DA-CCYYMMDD-R   07020000
007030            MOVE MM   OF DA-DD-MM-CCYY TO MM   OF DA-CCYYMMDD-R   07030000
007040            MOVE DD   OF DA-DD-MM-CCYY TO DD   OF DA-CCYYMMDD-R   07040000
007050     END-EVALUATE                                                 07050000
007060     MOVE DA-CCYYMMDD-R TO DA-INVTR-FORM-AS OF VMBFAS             07060000
007070     MOVE RA-QZTTIFS-479BFAS OF DCLDZBFASTV TO                    07070000
007080          RA-QZTTI-FORM-AS OF VMBFAS                              07080000
007090     MOVE RA-DGTTIFS-479BFAS OF DCLDZBFASTV TO                    07090000
007100          RA-DGTTI-FORM-AS OF VMBFAS                              07100000
007110     MOVE NB-DGTTIFS-479BFAS OF DCLDZBFASTV TO                    07110000
007120          NB-DGTTI-FORM-AS OF VMBFAS                              07120000
007130     MOVE AM-DGTTIFS-479BFAS OF DCLDZBFASTV TO                    07130000
007140          AM-DGTTI-FORM-AS OF VMBFAS                              07140000
007150     MOVE ST-DGTTIFS-479BFAS OF DCLDZBFASTV TO                    07150000
007160          ST-DGTTI-FORM-AS OF VMBFAS                              07160000
007170     MOVE ST-PRRWFS-479BFAS OF DCLDZBFASTV TO                     07170000
007180          ST-PRRW-FORM-AS OF VMBFAS                               07180000
007190     MOVE RA-GIFTFS-479BFAS OF DCLDZBFASTV TO                     07190000
007200          RA-GIFT-FORM-AS OF VMBFAS                               07200000
007210     MOVE AM-GIFTFS-479BFAS OF DCLDZBFASTV TO                     07210000
007220          AM-GIFT-FORM-AS OF VMBFAS                               07220000
007230     MOVE ST-VOORHFS-479BFAS OF DCLDZBFASTV TO                    07230000
007240          ST-VOORH-FORM-AS OF VMBFAS                              07240000
007250     MOVE DA-CPTAFS-479BFAS OF DCLDZBFASTV TO DA-DD-MM-CCYY       07250000
007260     EVALUATE TRUE                                                07260000
007270       WHEN DA-DD-MM-CCYY = '01.01.0001'                          07270000
007280            MOVE ZEROES TO DA-CCYYMMDD-R                          07280000
007290       WHEN DA-DD-MM-CCYY = '31.12.9999'                          07290000
007300            MOVE '99999999' TO DA-CCYYMMDD-R                      07300000
007310       WHEN OTHER                                                 07310000
007320            MOVE CCYY OF DA-DD-MM-CCYY TO CCYY OF DA-CCYYMMDD-R   07320000
007330            MOVE MM   OF DA-DD-MM-CCYY TO MM   OF DA-CCYYMMDD-R   07330000
007340            MOVE DD   OF DA-DD-MM-CCYY TO DD   OF DA-CCYYMMDD-R   07340000
007350     END-EVALUATE                                                 07350000
007360     MOVE DA-CCYYMMDD-R TO DA-CPTA-FORM-AS OF VMBFAS              07360000
007370     MOVE CO-EXTOBFS-479BFAS OF DCLDZBFASTV TO                    07370000
007380          CO-EXTOB-FORM-AS OF VMBFAS                              07380000
007390     MOVE CO-PLTOBFS-479BFAS OF DCLDZBFASTV TO                    07390000
007400          CO-PLTOB-FORM-AS OF VMBFAS                              07400000
007410     MOVE RA-TOBFS-479BFAS OF DCLDZBFASTV TO                      07410000
007420          RA-TOB-FORM-AS OF VMBFAS                                07420000
007430     MOVE AM-TOBFS-479BFAS OF DCLDZBFASTV TO                      07430000
007440          AM-TOB-FORM-AS OF VMBFAS                                07440000
007450     MOVE RA-TARPHFS-479BFAS OF DCLDZBFASTV TO                    07450000
007460          RA-TARPH-FORM-AS OF VMBFAS                              07460000
007470     MOVE AM-TARPH-479BFAS OF DCLDZBFASTV TO                      07470000
007480          AM-TARPH-FORM-AS OF VMBFAS                              07480000
007490     MOVE AM-BASEFS-479BFAS OF DCLDZBFASTV TO                     07490000
007500          AM-BASE-FORM-AS OF VMBFAS                               07500000
007510     MOVE AM-FLKFS-479BFAS OF DCLDZBFASTV TO                      07510000
007520          AM-FLK-FORM-AS OF VMBFAS                                07520000
007530     MOVE NR-ISFMAS-479BFAS OF DCLDZBFASTV                        07530000
007540                        TO W-NR-IS-FORM-AS                        07540000
007550     MOVE W-NR-ID-ISSUE TO F-NR-IS                                07550000
007560     MOVE NR-STFMAS-479BFAS OF DCLDZBFASTV                        07560000
007570                        TO F-NR-ST                                07570000
007580     WRITE FORM-REC FROM REC-FORM.                                07580000
007590                                                                  07590000
007600 BEHANDELING-EXIT.                                                07600000
007610*                                                                 07610000
007620     EXIT.                                                        07620000
007630*                                                                 07630000
007640*                                                                 07640000
007650 EINDE-PROGRAMMA.                                                 07650000
007660*----------------                                                 07660000
007670     CLOSE FORM.                                                  07670000
007680*                                                                 07680000
007690 EINDE-PROGRAMMA-EXIT.                                            07690000
007700*                                                                 07700000
007710     EXIT.                                                        07710000
007720/                                                                 07720000
007730                                                                  07730000
007740*DB2 GENERATED CURSOR OPEN FETCH CLOSE PARAGRAPHS              *  07740000
007750                                                                  07750000
007760 710-OPEN-DZBFASC1.                                               07760000
007770D    DISPLAY '710-OPEN-DZBFASC1.'                                 07770000
007780     MOVE 710    TO SQL-LOCATION                                  07780000
007790                                                                  07790000
007800     EXEC SQL                                                     07800000
007810       OPEN DZBFASC1                                              07810000
007820     END-EXEC                                                     07820000
007830                                                                  07830000
007840     EVALUATE SQLCODE                                             07840000
007850       WHEN ZERO                                                  07850000
007860            SET DZBFASC1-NOT-EOC TO TRUE                          07860000
007870       WHEN OTHER                                                 07870000
007880            DISPLAY 'ERROR WHILE OPENING CURSOR DZBFASC1'         07880000
007890            PERFORM SQLERROR                                      07890000
007900     END-EVALUATE                                                 07900000
007910     .                                                            07910000
007920                                                                  07920000
007930 720-FETCH-DZBFASC1.                                              07930000
007940D    DISPLAY '720-FETCH-DZBFASC1.'                                07940000
007950     SET DZBFASC1-NOT-EOC TO TRUE                                 07950000
007960     MOVE 720    TO SQL-LOCATION                                  07960000
007970                                                                  07970000
007980     EXEC SQL                                                     07980000
007990       FETCH DZBFASC1                                             07990000
008000        INTO :DCLDZBFASTV.DA-CPTAFS-479BFAS                       08000000
008010           , :DCLDZBFASTV.DA-CRFMAS-479BFAS                       08010000
008020           , :DCLDZBFASTV.NR-ISFMAS-479BFAS                       08020000
008030           , :DCLDZBFASTV.NR-STFMAS-479BFAS                       08030000
008040           , :DCLDZBFASTV.CT-RKTGDSV-479BFAS                      08040000
008050           , :DCLDZBFASTV.NR-CIOFMAS-479BFAS                      08050000
008060           , :DCLDZBFASTV.NR-IDFMAS-479BFAS                       08060000
008070           , :DCLDZBFASTV.CT-OPD-479BFAS                          08070000
008080           , :DCLDZBFASTV.CT-OPG-479BFAS                          08080000
008090           , :DCLDZBFASTV.NR-CIWFMAS-479BFAS                      08090000
008100           , :DCLDZBFASTV.DA-VAFMAS-479BFAS                       08100000
008110           , :DCLDZBFASTV.CO-VMFMAS-479BFAS                       08110000
008120           , :DCLDZBFASTV.RA-RTFMAS-479BFAS                       08120000
008130           , :DCLDZBFASTV.RA-CPFMAS-479BFAS                       08130000
008140           , :DCLDZBFASTV.RA-BASFMAS-479BFAS                      08140000
008150           , :DCLDZBFASTV.DA-UBFMAS-479BFAS                       08150000
008160           , :DCLDZBFASTV.DA-UEFMAS-479BFAS                       08160000
008170           , :DCLDZBFASTV.DU-STFMAS-479BFAS                       08170000
008180           , :DCLDZBFASTV.RA-PSFMAS-479BFAS                       08180000
008190           , :DCLDZBFASTV.RA-PRFMAS-479BFAS                       08190000
008200           , :DCLDZBFASTV.AM-CNSFMAS-479BFAS                      08200000
008210           , :DCLDZBFASTV.AM-PSFMAS-479BFAS                       08210000
008220           , :DCLDZBFASTV.NB-FIFMAS-479BFAS                       08220000
008230           , :DCLDZBFASTV.AM-FINFMAS-479BFAS                      08230000
008240           , :DCLDZBFASTV.CO-RIFMAS-479BFAS                       08240000
008250           , :DCLDZBFASTV.NR-IDRFMAS-479BFAS                      08250000
008260           , :DCLDZBFASTV.DA-UERFMAS-479BFAS                      08260000
008270           , :DCLDZBFASTV.AM-FBAFMAS-479BFAS                      08270000
008280           , :DCLDZBFASTV.AM-FBBFMAS-479BFAS                      08280000
008290           , :DCLDZBFASTV.CO-RMFMAS-479BFAS                       08290000
008300           , :DCLDZBFASTV.RA-FBFMAS-479BFAS                       08300000
008310           , :DCLDZBFASTV.NB-FBFMAS-479BFAS                       08310000
008320           , :DCLDZBFASTV.AM-FBNFMAS-479BFAS                      08320000
008330           , :DCLDZBFASTV.RA-TIFMAS-479BFAS                       08330000
008340           , :DCLDZBFASTV.AM-CNDFMAS-479BFAS                      08340000
008350           , :DCLDZBFASTV.AM-CNDNFAS-479BFAS                      08350000
008360           , :DCLDZBFASTV.AM-CNSNFAS-479BFAS                      08360000
008370           , :DCLDZBFASTV.NR-CDFMAS-479BFAS                       08370000
008380           , :DCLDZBFASTV.CT-SLFMAS-479BFAS                       08380000
008390           , :DCLDZBFASTV.CX-TWFMAS-479BFAS                       08390000
008400           , :DCLDZBFASTV.NR-DSFMAS-479BFAS                       08400000
008410           , :DCLDZBFASTV.NR-IDXFMAS-479BFAS                      08410000
008420           , :DCLDZBFASTV.CO-LAFMAS-479BFAS                       08420000
008430           , :DCLDZBFASTV.AM-INTFMAS-479BFAS                      08430000
008440           , :DCLDZBFASTV.NB-GRPFMAS-479BFAS                      08440000
008450           , :DCLDZBFASTV.NR-PRGRPFS-479BFAS                      08450000
008460           , :DCLDZBFASTV.NR-NEGRPFS-479BFAS                      08460000
008470           , :DCLDZBFASTV.NR-FIGRPFS-479BFAS                      08470000
008480           , :DCLDZBFASTV.NR-SEGRPFS-479BFAS                      08480000
008490           , :DCLDZBFASTV.NS-IDCPFS-479BFAS                       08490000
008500           , :DCLDZBFASTV.AM-CNSSPFS-479BFAS                      08500000
008510           , :DCLDZBFASTV.RA-CPTOTFS-479BFAS                      08510000
008520           , :DCLDZBFASTV.CO-CPFMAS-479BFAS                       08520000
008530           , :DCLDZBFASTV.CO-PERINFS-479BFAS                      08530000
008540           , :DCLDZBFASTV.NS-IDFMAS-479BFAS                       08540000
008550           , :DCLDZBFASTV.CO-DEVFMAS-479BFAS                      08550000
008560           , :DCLDZBFASTV.NB-KRDEVFS-479BFAS                      08560000
008570           , :DCLDZBFASTV.AM-BSDECFS-479BFAS                      08570000
008580           , :DCLDZBFASTV.CO-TYPFMAS-479BFAS                      08580000
008590           , :DCLDZBFASTV.CO-SUBTPFS-479BFAS                      08590000
008600           , :DCLDZBFASTV.CO-CONTFS-479BFAS                       08600000
008610           , :DCLDZBFASTV.CO-TPVGLFS-479BFAS                      08610000
008620           , :DCLDZBFASTV.AM-VGLFMAS-479BFAS                      08620000
008630           , :DCLDZBFASTV.NR-PRDFMAS-479BFAS                      08630000
008640           , :DCLDZBFASTV.DA-ACTVRFS-479BFAS                      08640000
008650           , :DCLDZBFASTV.DA-INVTRFS-479BFAS                      08650000
008660           , :DCLDZBFASTV.RA-QZTTIFS-479BFAS                      08660000
008670           , :DCLDZBFASTV.RA-DGTTIFS-479BFAS                      08670000
008680           , :DCLDZBFASTV.NB-DGTTIFS-479BFAS                      08680000
008690           , :DCLDZBFASTV.AM-DGTTIFS-479BFAS                      08690000
008700           , :DCLDZBFASTV.ST-DGTTIFS-479BFAS                      08700000
008710           , :DCLDZBFASTV.ST-PRRWFS-479BFAS                       08710000
008720           , :DCLDZBFASTV.RA-GIFTFS-479BFAS                       08720000
008730           , :DCLDZBFASTV.AM-GIFTFS-479BFAS                       08730000
008740           , :DCLDZBFASTV.ST-VOORHFS-479BFAS                      08740000
008750           , :DCLDZBFASTV.CO-EXTOBFS-479BFAS                      08750000
008760           , :DCLDZBFASTV.CO-PLTOBFS-479BFAS                      08760000
008770           , :DCLDZBFASTV.RA-TOBFS-479BFAS                        08770000
008780           , :DCLDZBFASTV.AM-TOBFS-479BFAS                        08780000
008790           , :DCLDZBFASTV.RA-TARPHFS-479BFAS                      08790000
008800           , :DCLDZBFASTV.AM-TARPH-479BFAS                        08800000
008810           , :DCLDZBFASTV.AM-BASEFS-479BFAS                       08810000
008820           , :DCLDZBFASTV.AM-FLKFS-479BFAS                        08820000
008830           , :DCLDZBFASTV.NR-CIOFMAS-479SIAS                      08830000
008840           , :DCLDZBFASTV.NR-IDFMAS-479SIAS                       08840000
008850           , :DCLDZBFASTV.NR-ID-479BFAS                           08850000
008860     END-EXEC                                                     08860000
008870                                                                  08870000
008880     EVALUATE SQLCODE                                             08880000
008890       WHEN ZERO                                                  08890000
008900            ADD 1 TO WS-NB-BFAS-COUNT                             08900000
008910            PERFORM BEHANDELING THRU BEHANDELING-EXIT             08910000
008920       WHEN 100                                                   08920000
008930            SET DZBFASC1-EOC TO TRUE                              08930000
008940       WHEN OTHER                                                 08940000
008950            DISPLAY 'ERROR WHILE FETCHING CURSOR DZBFASC1'        08950000
008960            PERFORM SQLERROR                                      08960000
008970     END-EVALUATE                                                 08970000
008980     .                                                            08980000
008990                                                                  08990000
009000 730-CLOSE-DZBFASC1.                                              09000000
009010D    DISPLAY '730-CLOSE-DZBFASC1.'                                09010000
009020     MOVE 730    TO SQL-LOCATION                                  09020000
009030                                                                  09030000
009040     EXEC SQL                                                     09040000
009050       CLOSE DZBFASC1                                             09050000
009060     END-EXEC                                                     09060000
009070                                                                  09070000
009080     EVALUATE SQLCODE                                             09080000
009090       WHEN ZERO                                                  09090000
009100            CONTINUE                                              09100000
009110       WHEN OTHER                                                 09110000
009120            DISPLAY 'ERROR WHILE CLOSING CURSOR DZBFASC1'         09120000
009130            PERFORM SQLERROR                                      09130000
009140     END-EVALUATE                                                 09140000
009150     .                                                            09150000
009160                                                                  09160000
009170                                                                  09170000
009180 600-GET-TIMESTAMP.                                               09180000
009190D    DISPLAY '600-GET-TIMESTAMP.'                                 09190000
009200     MOVE FUNCTION CURRENT-DATE            TO TS-SYSTEM.          09200000
009210     MOVE CC OF TS-SYSTEM             TO CC OF TS-TIMESTAMP       09210000
009220     MOVE YY OF TS-SYSTEM             TO YY OF TS-TIMESTAMP       09220000
009230     MOVE MM OF TS-SYSTEM             TO MM OF TS-TIMESTAMP       09230000
009240     MOVE DD OF TS-SYSTEM             TO DD OF TS-TIMESTAMP       09240000
009250     MOVE HH OF TS-SYSTEM             TO HH OF TS-TIMESTAMP       09250000
009260     MOVE MI OF TS-SYSTEM             TO MI OF TS-TIMESTAMP       09260000
009270     MOVE SS OF TS-SYSTEM             TO SS OF TS-TIMESTAMP       09270000
009280     MOVE TT OF TS-SYSTEM             TO TT OF TS-TIMESTAMP       09280000
009290     DISPLAY 'TIMESTAMP: ' TS-TIMESTAMP                           09290000
009300     .                                                            09300000
009310                                                                  09310000
009320*SQLERROR ROUTINE.                                                09320000
009330     EXEC SQL                                                     09330000
009340          INCLUDE SQLERROR                                        09340000
009350     END-EXEC.                                                    09350000
