package tests_handler

import (
	"encoding/json"
	"fmt"
	"github.com/xiaoshuwei/test/src/types/tests_types"
	"testing"
)

func TestTestsHandler(t *testing.T) {
	s := &tests_types.TestStruct{
		Name: "test",
		Age:  18,
	}
	data, err := json.Marshal(s)
	if err != nil {
		fmt.Printf("err: %v", err)
		return
	}
	fmt.Printf("data: %s", string(data))
}
