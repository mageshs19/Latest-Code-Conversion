000010 CBL NOCMPR2, NOFLAGMIG                                           00000010
000020 IDENTIFICATION DIVISION.                                         00000020
000030*------------------------                                         00000030
000040 PROGRAM-ID.     VM4BD420.                                        00000040
000050 AUTHOR.         M BEEVERS (DATA PROCESS).                        00000050
000060 DATE-WRITTEN.   JANUARI 1988.                                    00000060
000070*                                                                 00000070
000080******************************************************************00000080
000090*                                                                *00000090
000100*                INFORMATORISCHE KASBON 2.                       *00000100
000110*                                                                *00000110
000120******************************************************************00000120
000130*                                                                *00000130
000140*                VERGELIJKING DATABASE EN INVENTARIS             *00000140
000150*                -----------------------------------             *00000150
000160*                                                                *00000160
000170*                TWEEDE PROGRAMMA :                              *00000170
000180*                                                                *00000180
000190*                OPZOEKEN VAN ALLE EFFECTEN EN ALLE EVENEMENTEN  *00000190
000200*                DIE NOG IN LEVEN ZIJN.                          *00000200
000210*                                                                *00000210
000220* 01/06/92 : DE SCHEPPER KOEN (HCS AS) - PROBLEM RECORD 436451   *00000220
000230*            WAARDEN DIE NOG IN STOCK ZIJN MOGEN NIET MEEGENOMEN *00000230
000240*            WORDEN IN HET OUTPUTBESTAND.                        *00000240
000250*                                                                *00000250
000260* 16/06/92 : DE SCHEPPER KOEN (HCS AS) - PROBLEM RECORD 436451   *00000260
000270*            BIJVOEGEN PARMDATE + TEST OP DA-CRE-EVENT-PROD      *00000270
000280*                                                                *00000280
000290* 12/03/97 : HEYSE K. (SOFT GUIDE)                               *00000290
000300*            AANPASSINGEN EURO EN 2000                           *00000300
000310*            UITBREIDEN BEDRAGEN                                 *00000310
000320*            UITBREIDEN JAARTAL TOT 4 POS VOOR 2000              *00000320
000330*                                                                *00000330
000340* 04/03/98 : DE SCHEPPER KOEN - PROJECT 5421 : TESTWAARDEN       *00000340
000350*            CI CREATIE MEE DOORGEVEN NAAR VERVOLG OM DE         *00000350
000360*            SPLITSING TEST-REEEL TE KUNNEN DOEN                 *00000360
000370* J-M BOOGAERTS                                                  *00000370
000371* 2004/12 REPRENDRE N° DE TITRE EN OUTPUT (12 POS DE LIBRES)     *00000371
000372*                                                                *00000372
000373*                                                                *00000373
000380******************************************************************00000380
000390/                                                                 00000390
000400 ENVIRONMENT DIVISION.                                            00000400
000410*---------------------                                            00000410
000420 INPUT-OUTPUT SECTION.                                            00000420
000430 FILE-CONTROL.                                                    00000430
000440     SELECT UITBST ASSIGN TO UT-S-DD005.                          00000440
000450 IDMS-CONTROL SECTION.                                            00000450
000460 PROTOCOL. MODE IS BATCH DEBUG                                    00000460
000470           IDMS-RECORDS WITHIN WORKING-STORAGE SECTION.           00000470
000480/                                                                 00000480
000490 DATA DIVISION.                                                   00000490
000500*--------------                                                   00000500
000510 FILE SECTION.                                                    00000510
000520*                                                                 00000520
000530 FD  UITBST                                                       00000530
000540     BLOCK CONTAINS 0 RECORDS                                     00000540
000550     RECORD CONTAINS 50 CHARACTERS                                00000550
000560     RECORDING MODE F                                             00000560
000570     LABEL RECORDS STANDARD.                                      00000570
000580 01  UITRECORD.                                                   00000580
000610     03  UIT-AM-CN-STOCK          PIC S9(13)V99 COMP-3.           00000610
000620     03  UIT-AM-CND-STOCK         PIC S9(13)V99 COMP-3.           00000620
000630     03  UIT-NR-CIO-CRE           PIC 9(6).                       00000630
000640     03  UIT-NR-ID                PIC X(04).                      00000640
000641     03  UIT-NS-SEQ               PIC 9(04).                      00000641
000642     03  UIT-DA-UBSEC             PIC X(08).                      00000642
000643     03  UIT-NR-ST                PIC X(12).                      00000643
000650*                                                                 00000650
000660 SCHEMA SECTION.                                                  00000660
000670 DB  VMBTS07 WITHIN VMBTSCH.                                      00000670
000680*                                                                 00000680
000690 WORKING-STORAGE SECTION.                                         00000690
000700*                                                                 00000700
000710 01  WS-TE-WORK.                                                  00000710
000720     10  WS-STATUS                PIC X    VALUE SPACE.           00000720
000730     10  USERABEN                 PIC X(8) VALUE 'USERABEN'.      00000730
000740     10  WS-NR-ID-GOOD.                                           00000740
000750         20  WS-NR-CIO-CRE        PIC 9(8) COMP-3.                00000750
000760         20  WS-DA-CR-CRE         PIC 9(8) COMP-3.                00000760
000770         20  WS-NR-ID-CRE         PIC 9(6) COMP-3.                00000770
000780         20  WS-CT-OPD-CRE        PIC S9(3) COMP-3.               00000780
000790         20  WS-CT-OPG-CRE        PIC 9(3) COMP-3.                00000790
000800         20  FILLER               PIC X(2).                       00000800
000810*                                                                 00000810
000820*----- FIELDS ESDATMAS ------------------------------------------*00000820
000830     COPY ESDATMAS.                                               00000830
000840*----- FIELDS PARAMETER DATE ------------------------------------*00000840
000850 01  ZONE-DATONLY.                                                00000850
000860     03  DATE6R-WS.                                               00000860
000870         05  D-YEAR               PIC 99.                         00000870
000880         05  D-MONTH              PIC 99.                         00000880
000890         05  D-DAY                PIC 99.                         00000890
000900     03  DATE6 REDEFINES DATE6R-WS.                               00000900
000910         05  D-DAY                PIC 99.                         00000910
000920         05  D-MONTH              PIC 99.                         00000920
000930         05  D-YEAR               PIC 99.                         00000930
000940     03  DATE8.                                                   00000940
000950         05  D-DAY                PIC 99.                         00000950
000960         05  D-MONTH              PIC 99.                         00000960
000970         05  D-CENT               PIC 99.                         00000970
000980         05  D-YEAR               PIC 99.                         00000980
000990     03  PARMDATE.                                                00000990
001000         05  D-YEAR               PIC 9(4).                       00001000
001010         05  D-MONTH              PIC 9(2).                       00001010
001020         05  D-DAY                PIC 9(2).                       00001020
001030*                                                                 00001030
001040 LINKAGE SECTION.                                                 00001040
001050 01  PARAM-DATONLY.                                               00001050
001060     03  L-PARAM                  PIC S9(4) COMP.                 00001060
001070     03  DATUMLS.                                                 00001070
001080         05  DATE-IND             PIC X.                          00001080
001090         05  DATE8-LS             PIC X(8).                       00001090
001100     EJECT                                                        00001100
001110 PROCEDURE DIVISION USING PARAM-DATONLY.                          00001110
001120*                                                                 00001120
001130* INITIALISATIE                                                   00001130
001140*                                                                 00001140
001150     IF DATE-IND = '0'                                            00001150
001160         ACCEPT DATE6R-WS FROM DATE                               00001160
001170         MOVE CORR DATE6R-WS      TO DATE8                        00001170
001180         IF D-YEAR OF DATE8 > 60                                  00001180
001190              MOVE 19 TO D-CENT OF DATE8                          00001190
001200         ELSE MOVE 20 TO D-CENT OF DATE8                          00001200
001210         END-IF                                                   00001210
001220         MOVE CORR DATE8          TO DATE6                        00001220
001230     ELSE                                                         00001230
001240         MOVE DATE8-LS            TO DATE8                        00001240
001250         MOVE CORR DATE8          TO DATE6                        00001250
001260     END-IF.                                                      00001260
001270     MOVE  DATE6                 TO ES-DATUM.                     00001270
001280     MOVE  ZEROES                TO ES-DAGEN, ES-TYPE-DAG.        00001280
001290     MOVE  '+'                   TO ES-PLUS-MIN.                  00001290
001300*                                                                 00001300
001310     CALL ESDATMAS USING ES-DATUM ES-DAGEN ES-TYPE-DAG ES-PLUS-MIN00001310
001320                         ES-ANTWOORD ES-RETURN-CODE ES-WERKZONE.  00001320
001330*                                                                 00001330
001340     IF ES-RETURN-CODE = '0'                                      00001340
001350          MOVE ES-JJJJ             TO D-YEAR OF PARMDATE          00001350
001360          MOVE ES-MM               TO D-MONTH OF PARMDATE         00001360
001370          MOVE ES-DD               TO D-DAY  OF PARMDATE          00001370
001380     ELSE DISPLAY '***********************************'           00001380
001390          DISPLAY ' '                                             00001390
001400          DISPLAY 'PARAMETER DATE IN ERROR = ' DATE6              00001400
001410          DISPLAY ' '                                             00001410
001420          DISPLAY '***********************************'           00001420
001430          CALL USERABEN                                           00001430
001440     END-IF.                                                      00001440
001450*                                                                 00001450
001460     MOVE 'VM4BD420' TO PROGRAM-NAME.                             00001460
001470     BIND RUN-UNIT                                                00001470
001480     PERFORM IDMS-STATUS                                          00001480
001490     BIND VMBEFF.                                                 00001490
001500     PERFORM IDMS-STATUS                                          00001500
001510     BIND VMBEVEF.                                                00001510
001520     PERFORM IDMS-STATUS                                          00001520
001530     READY AR-VMBEFF1 USAGE-MODE IS RETRIEVAL.                    00001530
001540     PERFORM IDMS-STATUS                                          00001540
001550     OPEN OUTPUT UITBST.                                          00001550
001560                                                                  00001560
001570     OBTAIN FIRST VMBEFF WITHIN AR-VMBEFF1.                       00001570
001580*                                                                 00001580
001590* HOOFDVERWERKING                                                 00001590
001600*                                                                 00001600
001610     PERFORM HOOFDVERWERKING                                      00001610
001620       UNTIL DB-END-OF-SET.                                       00001620
001630*                                                                 00001630
001640* EINDVERWERKING                                                  00001640
001650*                                                                 00001650
001660     CLOSE UITBST.                                                00001660
001670     FINISH                                                       00001670
001680     STOP RUN.                                                    00001680
001690/                                                                 00001690
001700 HOOFDVERWERKING.                                                 00001700
001710*                                                                 00001710
001720* OPZOEKEN VAN ALLE EVENEMENTEN BIJ EEN EFFECT                    00001720
001730*                                                                 00001730
001740     PERFORM IDMS-STATUS                                          00001740
001750     MOVE SPACE TO WS-STATUS                                      00001750
001760     OBTAIN FIRST VMBEVEF WITHIN VMBEFF-VMBEVEF                   00001760
001770     PERFORM VERWERK-VMBEVEF                                      00001770
001780       UNTIL DB-END-OF-SET.                                       00001780
001790*                                                                 00001790
001800* OPZOEKEN VAN VOLGEND EFFECT IN DE AREA                          00001800
001810*                                                                 00001810
001820     FIND CURRENT VMBEFF                                          00001820
001830     PERFORM IDMS-STATUS                                          00001830
001840     OBTAIN NEXT VMBEFF WITHIN AR-VMBEFF1.                        00001840
001850*                                                                 00001850
001860 VERWERK-VMBEVEF.                                                 00001860
001870     PERFORM IDMS-STATUS                                          00001870
001880     IF DA-CR-EVENT-PROD OF VMBEVEF NOT > PARMDATE                00001880
001890          IF CT-RK-TEVPR OF VMBEVEF = '0060' AND                  00001890
001900             WS-STATUS NOT = 'D'                                  00001900
001910               MOVE 'C' TO WS-STATUS                              00001910
001920               MOVE NR-ID-GOOD    TO WS-NR-ID-GOOD                00001920
001930          ELSE                                                    00001930
001940               IF CT-RK-TEVPR OF VMBEVEF = '0168' AND             00001940
001950                  CO-STATE-EVPRAN NOT = '1'                       00001950
001960                    MOVE 'D' TO WS-STATUS                         00001960
001970                    MOVE '0307' TO ERROR-STATUS                   00001970
001980               ELSE                                               00001980
001990                    IF CT-RK-TEVPR OF VMBEVEF = '0217' AND        00001990
002000                       WS-STATUS = SPACE                          00002000
002010                         MOVE 'S' TO WS-STATUS                    00002010
002020                    END-IF                                        00002020
002030               END-IF                                             00002030
002040          END-IF                                                  00002040
002050     END-IF.                                                      00002050
002060     IF NOT DB-END-OF-SET                                         00002060
002070          OBTAIN NEXT VMBEVEF WITHIN VMBEFF-VMBEVEF               00002070
002080          IF DB-END-OF-SET                                        00002080
002090               IF WS-STATUS = 'C'                                 00002090
002100                   MOVE AM-CN-STOCK  OF VMBEFF TO UIT-AM-CN-STOCK 00002100
002110                   MOVE AM-CND-STOCK OF VMBEFF TO UIT-AM-CND-STOCK00002110
002140                   MOVE WS-NR-CIO-CRE          TO UIT-NR-CIO-CRE  00002140
002142                   MOVE CO-IDPRKB-STOCK  OF VMBEFF TO UIT-NR-ID   00002142
002144                   MOVE NS-IRMO-STOCK    OF VMBEFF TO UIT-NS-SEQ  00002144
002146                   MOVE DA-UBSECIS-STOCK OF VMBEFF TO UIT-DA-UBSEC00002146
002147                   MOVE NR-ID-STOCK-R2   OF VMBEFF TO UIT-NR-ST   00002147
002150                   WRITE UITRECORD                                00002150
002160               END-IF                                             00002160
002170          END-IF                                                  00002170
002180     END-IF.                                                      00002180
002190/                                                                 00002190
002200 IDMS-ABORT.                                                      00002200
002210     EXIT.                                                        00002210
002220     COPY IDMS IDMS-STATUS.                                       00002220
