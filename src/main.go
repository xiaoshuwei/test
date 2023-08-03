package src

import (
	"database/sql"
	"fmt"
	_ "github.com/go-sql-driver/mysql"
)

func main() {
	//"username:password@[protocol](address:port)/database"
	db, _ := sql.Open("mysql", "dump:111@tcp(127.0.0.1:6001)") // Set database connection
	defer db.Close()                                           //Close DB
	err := db.Ping()                                           //Connect to DB
	if err != nil {
		fmt.Println("Database Connection Failed") //Connection failed
		return
	} else {
		fmt.Println("Database Connection Succeed") //Connection succeed
	}
}
