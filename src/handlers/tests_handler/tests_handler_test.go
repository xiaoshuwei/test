package tests_handler

import (
	"fmt"
	validator "github.com/go-playground/validator/v10"
	_ "github.com/go-sql-driver/mysql"
	"testing"
	"time"
)

func TestTestsHandler(t *testing.T) {
	tn := time.Now()
	t8 := tn.In(time.FixedZone("CST", 8*60*60))
	t0 := tn.In(time.FixedZone("CST", 0))
	fmt.Println(t8)
	fmt.Println(t0)
}

func testDeferFuncError() (err error) {
	defer func() {
		err = fmt.Errorf("defer error")
	}()
	err = fmt.Errorf("return error")
	return
}

func TestGinValidatorBindingStruct(t *testing.T) {
	validate := validator.New()
	validate.RegisterStructValidation(NameLengthValidation, T2{})

	t2 := &T2{
		Name: "shor123123t",
	}

	err := validate.Struct(t2)
	if err != nil {
		panic(err)
	}
}

type T2 struct {
	Name string `json:"name,omitempty"`
}

func NameLengthValidation(sl validator.StructLevel) {
	t := sl.Current().Interface().(T2)

	if len(t.Name) > 5 {
		sl.ReportError(t.Name, "name", "Name", "namelength", "")
	}
}

func TestDBConnection(t *testing.T) {
	fmt.Println(time.Now())
	fmt.Println(time.Now().UTC())
}

func TestCrypto(t *testing.T) {
	metaDBHost := "127.0.0.1"
	metaDBPort := 8001
	metaDBUserString := "username"
	metaDBPasswordString := "password"
	region := "us-west"
	authFrontendLoginUrl := "127.0.0.1:8002"
	configData := `metaDB:
    host: ` + metaDBHost + `
    port: ` + fmt.Sprintf("%d", metaDBPort) + `
    username: ` + metaDBUserString + `
    password: ` + metaDBPasswordString + `
    database: mocloud_meta
adminDB:
	host: ` + metaDBHost + `
    port: ` + fmt.Sprintf("%d", metaDBPort) + `
    username: ` + metaDBUserString + `
    password: ` + metaDBPasswordString + `
    database: mocadmin
log:
    level: debug
    format: json
    filename:
    maxSize:
    maxDays:
    MaxBackups:
server:
    host: localhost
    port: 8001
    certPath:
    env: dev
    accessTokenEffectiveTime: 24h
    privateKeyFile: /etc/keys/private.key
    publicKeyFile: /etc/keys/public.key
    kubeconfigFile: /etc/kube/kubeconfig
    region: ` + region + `
    frontendLoginUrl: ` + authFrontendLoginUrl + `
    priceUnit:
      aliyun-cn-hangzhou-rmb:
        cu: 500000
        storage: 0.025
`
	fmt.Println(configData)
}
