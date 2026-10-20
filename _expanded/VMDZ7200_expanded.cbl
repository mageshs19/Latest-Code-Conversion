000010 IDENTIFICATION DIVISION.                                         00000010
000020*========================                                         00000020
000030 PROGRAM-ID. VM7BD200.                                            00000030
000040 AUTHOR.   J-M BOOGAERTS  88/07.                                  00000040
000050                                                                  00000050
000060******************************************************************00000060
000070*                                                                 00000070
000080*    ARCHIVAGE :  EXTRACT DES FORMULAIRES A ARCHIVER              00000080
000090*    =========    (SOUSCRIPTIONS ET ANNULATIONS SOUSCRIPTIONS)    00000090
000100*                                                                 00000100
000110* WULTEPUTTE KRISTINE : (10/7/91) :                               00000110
000120*                                                                 00000120
000130* TOEVOEGEN VAN NIEUWE PLAGES VOOR BCI1                           00000130
000140*                                                                 00000140
000150* DE SCHEPPER KOEN    : (18/12/92) :                              00000150
000160*                                                                 00000160
000170* AANPASSING VOOR SLIK : UITBREIDING FORM 270 -> 390              00000170
000180*                                                                 00000180
000190* CLEMENT J. (06/93) : TOEVOEGEN PLAGES                           00000190
000200*                                                                 00000200
000210* DE SCHEPPER KOEN     (04/02/94) :                               00000210
000220*    PROGRAMMA VOLLEDIG HERSCHREVEN : GEEN SELECTIE OP            00000220
000230*    WAARDECODE MEER.                                             00000230
000240*                                                                 00000240
000250* POMPONIO S (03/97)                                              00000250
000260*    AANPASSING EURO2000 : PARMDATE EN 8 POSITIONS                00000260
000270*                          RECORD VMBFAS 388 -> 432 BYTES         00000270
000280*                                                                 00000280
000281* J-M BOOGAERTS 2005/02                                           00000281
000282*    INTÉGRATION ARCHIVAGE IUNS P8                                00000282
000283*                                                                 00000283
000290******************************************************************00000290
000300                                                                  00000300
000310 ENVIRONMENT DIVISION.                                            00000310
000320*=====================                                            00000320
000330 CONFIGURATION SECTION.                                           00000330
000340*----------------------                                           00000340
000350 SPECIAL-NAMES.                                                   00000350
000360     DECIMAL-POINT IS COMMA.                                      00000360
000370*                                                                 00000370
000380 INPUT-OUTPUT SECTION.                                            00000380
000390*---------------------                                            00000390
000400 FILE-CONTROL.                                                    00000400
000401     SELECT DAARCH   ASSIGN TO UT-S-DD005.                        00000401
000410     SELECT FORM     ASSIGN TO UT-S-DD010.                        00000410
000420*                                                                 00000420
000430 IDMS-CONTROL SECTION.                                            00000430
000440*---------------------                                            00000440
000450 PROTOCOL. MODE IS BATCH-AUTOSTATUS DEBUG                         00000450
000460           IDMS-RECORDS MANUAL.                                   00000460
000470/                                                                 00000470
000480 DATA DIVISION.                                                   00000480
000490*==============                                                   00000490
000500 FILE SECTION.                                                    00000500
000510*-------------                                                    00000510
000511*    ----- DATE ARCHIVAGE -----                                   00000511
000512*                                                                 00000512
000513 FD  DAARCH     RECORDING F                                       00000513
000514                RECORD CONTAINS 20                                00000514
000515                BLOCK CONTAINS 0                                  00000515
000516                LABEL RECORD STANDARD.                            00000516
000517 01  DAARCH-REC                PIC X(20).                         00000517
000520*                                                                 00000520
000530*    ----- GESELECTEERDE FORMULIEREN -----                        00000530
000540*                                                                 00000540
000550 FD  FORM       RECORDING F                                       00000550
000560                RECORD CONTAINS 530                               00000560
000570                BLOCK CONTAINS 0                                  00000570
000580                LABEL RECORD STANDARD.                            00000580
000590 01  FORM-REC                  PIC X(530).                        00000590
000600/                                                                 00000600
000610 SCHEMA SECTION.                                                  00000610
000620*---------------                                                  00000620
000630 DB VMBTS03  WITHIN VMBTSCH.                                      00000630
000640*                                                                 00000640
000650 WORKING-STORAGE SECTION.                                         00000650
000660*------------------------                                         00000660
000670*                                                                 00000670
000680 77  USERABEN                  PIC X(8)   VALUE 'USERABEN'.       00000680
000690 77  WS-TELLER                 PIC S9(11) COMP-3 VALUE ZERO.      00000690
000700*                                                                 00000700
000710 01  W-NR-IS-FORM-AS           PIC 9(9).                          00000710
000720 01  FILLER REDEFINES W-NR-IS-FORM-AS.                            00000720
000730     05  W-NR-ID-ISSUE         PIC 9(7).                          00000730
000740     05  W-NR-CD-ISSUE         PIC 9(2).                          00000740
000750*                                                                 00000750
000760 01  REC-FORM.                                                    00000760
000770     05  F-FORM                PIC X(478).                        00000770
000780     05  F-SW-ARCH             PIC X.                             00000780
000790     05  F-SW-VMBFGD           PIC X.                             00000790
000800     05  F-TELLER              PIC S9(11) COMP-3.                 00000800
000810     05  F-NR-IS               PIC 9(7).                          00000810
000811     05  F-NR-ST               PIC 9(13).                         00000811
000820     05  FILLER                PIC X(24).                         00000820
000830*                                                                 00000830
000831 COPY VMBZ270I.                                                   00000831
000840*                                                                 00000840
000850 01  WS-DATUMS.                                                   00000850
000860     02  DATE-YMD.                                                00000860
000870         03  D-YEAR            PIC 9(2).                          00000870
000880         03  D-MONTH           PIC 9(2).                          00000880
000890         03  D-DAY             PIC 9(2).                          00000890
000900     02  DATE-YMD8.                                               00000900
000910         03  D-CENT            PIC 9(2).                          00000910
000920         03  D-YEAR            PIC 9(2).                          00000920
000930         03  D-MONTH           PIC 9(2).                          00000930
000940         03  D-DAY             PIC 9(2).                          00000940
000950     02  DATE-DMY8.                                               00000950
000960         03  D-DAY             PIC 9(2).                          00000960
000970         03  D-MONTH           PIC 9(2).                          00000970
000980         03  D-CENT            PIC 9(2).                          00000980
000990         03  D-YEAR            PIC 9(2).                          00000990
001000*                                                                 00001000
001190/                                                                 00001190
001200 COPY IDMS SUBSCHEMA-CTRL.                                        00001200
001210*                                                                 00001210
001220 COPY IDMS SUBSCHEMA-LR-CTRL.                                     00001220
001230*                                                                 00001230
001240 COPY IDMS SUBSCHEMA-SSNAME.                                      00001240
001250*                                                                 00001250
001260 COPY IDMS SUBSCHEMA-RECNAMES.                                    00001260
001270*                                                                 00001270
001280 COPY IDMS SUBSCHEMA-SETNAMES.                                    00001280
001290*                                                                 00001290
001300 COPY IDMS SUBSCHEMA-AREANAMES.                                   00001300
001310*                                                                 00001310
001320 COPY IDMS LR VMBTL03-R01.                                        00001320
001330/                                                                 00001330
001340 LINKAGE SECTION.                                                 00001340
001350 01  PARAM-ZONEDO.                                                00001350
001360     02  L-PARAM          PIC S9(4)   COMP.                       00001360
001370     02  DATUMLS.                                                 00001370
001380         03  DATE-IND     PIC X.                                  00001380
001390         03  DATE8-LS     PIC 9(8).                               00001390
001400/                                                                 00001400
001410 PROCEDURE DIVISION USING PARAM-ZONEDO.                           00001410
001420*======================================                           00001420
001430     PERFORM BEGIN-PROGRAMMA THRU BEGIN-PROGRAMMA-EXIT.           00001430
001440     PERFORM BEHANDELING THRU BEHANDELING-EXIT                    00001440
001450             UNTIL DB-END-OF-SET.                                 00001450
001460     PERFORM EINDE-PROGRAMMA THRU EINDE-PROGRAMMA-EXIT.           00001460
001470*                                                                 00001470
001480     GOBACK.                                                      00001480
001490*                                                                 00001490
001500*                                                                 00001500
001510 BEGIN-PROGRAMMA.                                                 00001510
001520*----------------                                                 00001520
001530     IF DATE-IND = '0'                                            00001530
001540        ACCEPT DATE-YMD         FROM DATE                         00001540
001550        MOVE CORR DATE-YMD    TO DATE-DMY8                        00001550
001560        IF D-YEAR OF DATE-YMD > 60                                00001560
001570           MOVE 19            TO D-CENT OF DATE-DMY8              00001570
001580        ELSE                                                      00001580
001590           MOVE 20            TO D-CENT OF DATE-DMY8              00001590
001600        END-IF                                                    00001600
001610     ELSE                                                         00001610
001620        MOVE DATE8-LS         TO DATE-DMY8                        00001620
001630        MOVE CORR DATE-DMY8   TO DATE-YMD                         00001630
001640     END-IF.                                                      00001640
001650     MOVE CORR DATE-DMY8      TO DATE-YMD8.                       00001650
001660                                                                  00001660
001690*                                                                 00001690
001830     MOVE SPACES TO REC-FORM.                                     00001830
001840*                                                                 00001840
001850     OPEN INPUT  DAARCH                                           00001850
001851          OUTPUT FORM.                                            00001851
001852     READ DAARCH INTO VMBZ270I-REC                                00001852
001853          AT END                                                  00001853
001854             DISPLAY 'VM7BD200: ** DATE ARCHIVAGE NOT OK **'      00001854
001855             CALL USERABEN.                                       00001855
001856     DISPLAY 'DATE ARCH : ' DA-ARCH-YMD.                          00001856
001857     CLOSE DAARCH.                                                00001857
001860*                                                                 00001860
001870     MOVE 'VM7BD200'          TO PROGRAM-NAME.                    00001870
001880     BIND RUN-UNIT.                                               00001880
001890     BIND VMBFAS.                                                 00001890
001900     READY AR-VMBFRM1 USAGE-MODE IS RETRIEVAL                     00001900
001910*                                                                 00001910
001920*DB2: Expanded LRF FIRST VMBTL03-R01 WHERE SWEEP-VMBFAS -> VMBFAS 00001920
001920*  WITHIN AR-VMBFRM1.                                             00001920
001920     OBTAIN FIRST VMBFAS WITHIN AR-VMBFRM1.                       00001920
001930*                                                                 00001930
001940 BEGIN-PROGRAMMA-EXIT.                                            00001940
001950*                                                                 00001950
001960     EXIT.                                                        00001960
001970*                                                                 00001970
001980*                                                                 00001980
001990 BEHANDELING.                                                     00001990
002000*------------                                                     00002000
002010     IF (DA-CPTA-FORM-AS OF VMBFAS < DA-ARCH-YMD  AND             00002010
002020         DA-CPTA-FORM-AS OF VMBFAS NOT = '00000000') OR           00002020
002021        (DA-CR-FORM-AS OF VMBFAS < DA-ARCH-YMD AND                00002021
002022         DA-CPTA-FORM-AS OF VMBFAS = '00000000')                  00002022
002030           ADD 1              TO WS-TELLER                        00002030
002040           MOVE WS-TELLER     TO F-TELLER                         00002040
002050           MOVE VMBFAS        TO F-FORM                           00002050
002060           MOVE NR-IS-FORM-AS OF VMBFAS                           00002060
002070                              TO W-NR-IS-FORM-AS                  00002070
002080           MOVE W-NR-ID-ISSUE TO F-NR-IS                          00002080
002081           MOVE NR-ST-FORM-AS OF VMBFAS                           00002081
002082                              TO F-NR-ST                          00002082
002090           WRITE FORM-REC FROM REC-FORM                           00002090
002110     END-IF.                                                      00002110
002120*                                                                 00002120
002130*DB2: Expanded LRF NEXT VMBTL03-R01 WHERE SWEEP-VMBFAS -> VMBFAS  00002130
002130*  WITHIN AR-VMBFRM1.                                             00002130
002130     OBTAIN NEXT VMBFAS WITHIN AR-VMBFRM1.                        00002130
002140*                                                                 00002140
002150 BEHANDELING-EXIT.                                                00002150
002160*                                                                 00002160
002170     EXIT.                                                        00002170
002180*                                                                 00002180
002190*                                                                 00002190
002200 EINDE-PROGRAMMA.                                                 00002200
002210*----------------                                                 00002210
002220     FINISH.                                                      00002220
002230     CLOSE FORM.                                                  00002230
002240*                                                                 00002240
002250 EINDE-PROGRAMMA-EXIT.                                            00002250
002260*                                                                 00002260
002270     EXIT.                                                        00002270
002280/                                                                 00002280
002290 IDMS-ABORT.                                                      00002290
002300     CLOSE FORM.                                                  00002300
002310*                                                                 00002310
002320     COPY IDMS IDMS-STATUS.                                       00002320
