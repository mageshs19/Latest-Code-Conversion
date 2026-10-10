000000* VERSION  1.0;
000200*
000300*************************************************************
000400*    COPY NAME = VMBZ270I                                   *
000500*    LRECL       : 20                                       *
      *    BESTAND MET DATUMS EN GEBRUIKTE PARAMETERS             *
      *    VOOR UITVOERING VAN NIEUWE ARCHIVERING                 *
000700*************************************************************     ¨SSN1.1.
000800*                                                                 ¨SSN1.1.
000900 01  VMBZ270I-REC .
001000     05  DA-PARM-YMD       PIC 9(8)   .
001000     05  NB-ARCH-YY        PIC 9(2)   .
001000     05  NB-ARCH-MM        PIC 9(2)   .
001000     05  DA-ARCH-YMD       PIC 9(8)   .
001200
004100*********************************************************         ¨SSN1.1.
004200* COMMENTAAR                                            *         ¨SSN1.1.
004300*********************************************************         ¨SSN1.1.
004200*  DA-PARM-YMD : DATUM UITVOERING ARCHIVERING           *         ¨SSN1.1.
004200*  NB-ARCH-YY  : PARAMETER JAAR ( X JAAR  IN VERLEDEN ) *         ¨SSN1.1.
004200*  NB-ARCH-MM  : PARAMETER MAAND( X MAAND IN VERLEDEN ) *         ¨SSN1.1.
004200*  NB-ARCH-YMD : DATUM ARCHIVERING (DATUM - XX-FACTOR ) *         ¨SSN1.1.
004400*********************************************************         ¨SSN1.1.
