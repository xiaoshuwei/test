package jwt_token

import (
	"fmt"
	"github.com/golang-jwt/jwt"
	"testing"
	"time"
)

func TestJWTToken(t *testing.T) {
	Init("./etc/private.key", "./etc/public.key")
	token, err := GenerateJWTToken("uid", "name", "email@email.com", time.Second*10)
	if err != nil {
		fmt.Printf("GenerateJWTToken err: %v", err)
		return
	}
	time.Sleep(20 * time.Second)
	ac, err := ParseToken(token)
	if err != nil {
		ve, _ := err.(*jwt.ValidationError)
		fmt.Printf("ParseToken err: %v", ((ve.Errors)&jwt.ValidationErrorExpired != 0))
	}
	fmt.Printf(ac.ToString())
}
