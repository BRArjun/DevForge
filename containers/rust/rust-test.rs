use std::io::{self, Write};

fn main() {
    print!("What is your name? ");
    io::stdout().flush().unwrap();
    
    let mut name = String::new();
    io::stdin().read_line(&mut name).unwrap();
    let name = name.trim();
    
    println!("Hello, {}!", name);
    
    print!("How old are you? ");
    io::stdout().flush().unwrap();
    
    let mut age_str = String::new();
    io::stdin().read_line(&mut age_str).unwrap();
    
    match age_str.trim().parse::<i32>() {
        Ok(age) => println!("In 10 years, you'll be {} years old!", age + 10),
        Err(_) => println!("That's not a valid age!"),
    }
}
