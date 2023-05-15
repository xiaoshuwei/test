package tests_handler

import (
	"fmt"
	"testing"

	validator "github.com/go-playground/validator/v10"
)

func TestTestsHandler(t *testing.T) {
	//defer func能否修改返回的error
	err := testDeferFuncError()
	fmt.Printf("err: %v\n", err)
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
