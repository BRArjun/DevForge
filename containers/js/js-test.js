const readline = require('readline').createInterface({
  input: process.stdin,
  output: process.stdout
});

function askName() {
  return new Promise(resolve => {
    readline.question('What is your name? ', name => {
      resolve(name);
    });
  });
}

function askAge() {
  return new Promise(resolve => {
    readline.question('How old are you? ', age => {
      resolve(age);
    });
  });
}

async function main() {
  const name = await askName();
  console.log(`Hello, ${name}!`);
  
  const age = await askAge();
  const numAge = parseInt(age);
  
  if (isNaN(numAge)) {
    console.log("That's not a valid age!");
  } else {
    console.log(`In 10 years, you'll be ${numAge + 10} years old!`);
  }
  
  readline.close();
}

main();
