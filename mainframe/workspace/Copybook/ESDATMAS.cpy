000040******************************************************************00000006
000050*                                                                *00000007
000060*                   ZONES VOOR ROUTINE ESDATMAS.                 *00000008
000070*                                                                *00000009
000070*    CALL ESDATMAS USING ES-DATUM                                *00000009
000070*                        ES-DAGEN                                *00000009
000070*                        ES-TYPE-DAG                             *00000009
000070*                        ES-PLUS-MIN                             *00000009
000070*                        ES-ANTWOORD                             *00000009
000070*                        ES-RETURN-CODE                          *00000009
000070*                        ES-WERKZONE.                            *00000009
000070*                                                                *00000009
000080******************************************************************00000010
      *                                                                 00000011
       01  ESDATMAS                    PIC X(8) VALUE 'ESDATMAS'.       00000012
       01  ESDAZONE.                                                    00000012
           02  ES-DATUM                PIC X(8).                        00000013
           02  ES-DAGEN                PIC X(3).                        00000014
           02  ES-TYPE-DAG             PIC X.                           00000015
           02  ES-PLUS-MIN             PIC X.                           00000015
           02  ES-ANTWOORD.                                             00000015
             03  ES-DAG-JUL.                                            00000014
               04  ES-DDD              PIC XXX.                         00000014
               04  ES-JJJJ             PIC X(4).                        00000014
             03  ES-DAG-GREG.                                           00000014
               04  ES-DD               PIC 99 VALUE 0.
               04  ES-MM               PIC 99 VALUE 0.
               04  SECULA              PIC 99 VALUE 0.
               04  ES-JJ               PIC 99 VALUE 0.
             03  ES-DAG-HORVAR         PIC X(4).                        00000014
             03  ES-DAG-NATUUR         PIC X.                           00000014
             03  ES-DAG-KWALITEIT      PIC X.                           00000014
             03  ES-DAG-JEF            PIC X.                           00000014
             03  ES-DAG-BEURS          PIC X.                           00000014
             03  ES-DAG-BANKHOL        PIC X.                           00000014
             03  ES-DAG-SPECIAAL       PIC X.                           00000014
           02  ES-RETURN-CODE          PIC X.                           00000015
           02  ES-WERKZONE             PIC X(600).                      00000015
      *---------------------------------------------------------
