package jwt_token

import (
	"crypto/rsa"
	"fmt"
	"github.com/golang-jwt/jwt"
	"github.com/xiaoshuwei/test/src/consts"
	"os"
	"time"
)

// AccountClaims Account jwt.StandardClaims
type AccountClaims struct {
	UID         string `json:"uid"`
	Name        string `json:"name"`
	Email       string `json:"email"`
	LoginMethod string `json:"login_method"`
	//standard claim
	jwt.StandardClaims
}

func (c AccountClaims) ToString() string {
	return fmt.Sprintf("{UID:%s,Name:%s,Email:%s,LoginMethod:%s,StandardClaims:{ExpiresAt:%d,IssuedAt:%d}}", c.UID, c.Name, c.Email, c.LoginMethod, c.StandardClaims.ExpiresAt, c.StandardClaims.IssuedAt)
}

type JwtConfig struct {
	privateKeyFile string
	publicKeyFile  string
	privateKey     *rsa.PrivateKey
	publicKey      *rsa.PublicKey
}

var config *JwtConfig

func Init(privateKeyFile, publicKeyFile string) {
	config = &JwtConfig{
		privateKeyFile: privateKeyFile,
		publicKeyFile:  publicKeyFile,
	}
	publicKeyByte, err := os.ReadFile(config.publicKeyFile)
	if err != nil {
		panic(err)
	}
	config.publicKey, err = jwt.ParseRSAPublicKeyFromPEM(publicKeyByte)
	if err != nil {
		fmt.Printf("jwt initialize failed, %v", err)
	}
	privateKeyByte, err := os.ReadFile(config.privateKeyFile)
	if err != nil {
		fmt.Printf("jwt initialize failed, %v", err)
	}
	config.privateKey, _ = jwt.ParseRSAPrivateKeyFromPEM(privateKeyByte)
}

func GenerateJWTToken(uid, name, email string, validDuration time.Duration) (string, error) {
	claims := &AccountClaims{
		UID:   uid,
		Name:  name,
		Email: email,
		StandardClaims: jwt.StandardClaims{
			Issuer:    consts.APPName,
			IssuedAt:  time.Now().Unix(),
			ExpiresAt: time.Now().Add(validDuration).Unix(),
		},
	}
	return generateToken(claims)
}

// generateToken generates token with custom effect time
func generateToken(claims *AccountClaims) (string, error) {
	//Generate token
	sign, err := jwt.NewWithClaims(jwt.SigningMethodRS256, claims).SignedString(config.privateKey)
	if err != nil {
		return "", err
	}
	return sign, nil
}

// ParseToken parses token infos
func ParseToken(tokenString string) (*AccountClaims, error) {
	//Parse token
	token, err := jwt.ParseWithClaims(tokenString, &AccountClaims{}, func(token *jwt.Token) (interface{}, error) {
		return config.publicKey, nil
	})
	//if err != nil {
	//	return nil, err
	//}
	claims, ok := token.Claims.(*AccountClaims)
	if !ok {
		panic("token is valid")
	}
	return claims, err
}
