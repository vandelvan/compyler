	START
;	ABA
;VAR2	ADCA #@30
	ORG $4000
;	ABA
PUERTA	EQU $1000
	ADDD 1,X
	ADDD 2,X
	ADDD -2,X
	ADDD -16,PC
;	BNE VAR2
;	BNE PUERTA
;	BNE FIN
	ADDD 200,SP
	ADDD -200,SP
FIN	END