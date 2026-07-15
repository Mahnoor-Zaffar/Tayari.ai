export const CODE_TEMPLATES: Record<string, string> = {
  python: `def solve():
    # Read input and return output
    pass

if __name__ == "__main__":
    result = solve()
    print(result)
`,
  javascript: `function solve(input) {
    // Your code here
    return input;
}

const readline = require('readline');
const rl = readline.createInterface({
    input: process.stdin,
    output: process.stdout
});
rl.on('line', (line) => {
    console.log(solve(line));
});
`,
  typescript: `function solve(input: string): string {
    // Your code here
    return input;
}

const readline = require('readline');
const rl = readline.createInterface({
    input: process.stdin,
    output: process.stdout
});
rl.on('line', (line: string) => {
    console.log(solve(line));
});
`,
  java: `public class Solution {
    public static void main(String[] args) {
        java.util.Scanner sc = new java.util.Scanner(System.in);
        while (sc.hasNextLine()) {
            String line = sc.nextLine();
            System.out.println(solve(line));
        }
    }
    
    public static String solve(String input) {
        // Your code here
        return input;
    }
}
`,
  cpp: `#include <iostream>
#include <string>
using namespace std;

string solve(string input) {
    // Your code here
    return input;
}

int main() {
    string line;
    while (getline(cin, line)) {
        cout << solve(line) << endl;
    }
    return 0;
}
`,
  go: `package main

import (
    "bufio"
    "fmt"
    "os"
)

func solve(input string) string {
    // Your code here
    return input
}

func main() {
    scanner := bufio.NewScanner(os.Stdin)
    for scanner.Scan() {
        fmt.Println(solve(scanner.Text()))
    }
}
`,
  rust: `use std::io::{self, BufRead};

fn solve(input: &str) -> String {
    // Your code here
    input.to_string()
}

fn main() {
    let stdin = io::stdin();
    for line in stdin.lock().lines() {
        if let Ok(l) = line {
            println!("{}", solve(&l));
        }
    }
}
`,
};

export const LANGUAGE_EXTENSIONS: Record<string, string> = {
  python: "py",
  javascript: "js",
  typescript: "ts",
  java: "java",
  cpp: "cpp",
  go: "go",
  rust: "rs",
};

export const LANGUAGE_MONACO_IDS: Record<string, string> = {
  python: "python",
  javascript: "javascript",
  typescript: "typescript",
  java: "java",
  cpp: "cpp",
  go: "go",
  rust: "rust",
};
