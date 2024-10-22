use std::io::{self, Write};
use colored::*;
use text_io::read;

fn main() {
    print!("{}", "What is your name? ".green());
    io::stdout().flush().unwrap();
    
    let name: String = read!("{}\n");
    
    println!("{}{}{}", "Hello, ".blue(), name.yellow(), "!".blue());
    
    print!("{}", "How old are you? ".green());
    io::stdout().flush().unwrap();
    
    let age: Result<i32, _> = read!();
    
    match age {
        Ok(n) => println!("{}", format!("In 10 years, you'll be {} years old!", n + 10).blue()),
        Err(_) => println!("{}", "That's not a valid age!".red()),
    }
}
