#include <Arduino.h>
#include <ArduinoJson.h>

const int BOARD_SIZE = 3;
char board[BOARD_SIZE][BOARD_SIZE];
char currentPlayer = 'X';
bool gameOver = false;
int gameMode = 0;

/**
 * @brief Initializes the TicTacToe board and resets game variables.
 * Sets all board positions to empty (' ') and sets the current player to 'X'.
 */
void initializeBoard() {
    for (int i = 0; i < BOARD_SIZE; i++) {
        for (int j = 0; j < BOARD_SIZE; j++) {
            board[i][j] = ' ';
        }
    }
    currentPlayer = 'X';
    gameOver = false;
}

/**
 * @brief Sends a JSON message over Serial.
 * 
 * @param type The type of message (e.g., "info", "error", "win_status").
 * @param message The message content.
 */
void sendJsonMessage(const char* type, const char* message) {
    StaticJsonDocument<200> doc;
    doc["type"] = type;
    doc["message"] = message;
    serializeJson(doc, Serial);
    Serial.println();
}

/**
 * @brief Sends the current state of the board over Serial as a JSON message.
 */
void sendBoardState() {
    StaticJsonDocument<300> doc;
    doc["type"] = "board";
    JsonArray boardArray = doc.createNestedArray("board");
    for (int i = 0; i < BOARD_SIZE; i++) {
        JsonArray row = boardArray.createNestedArray();
        for (int j = 0; j < BOARD_SIZE; j++) {
            row.add(String(board[i][j]));
        }
    }
    serializeJson(doc, Serial);
    Serial.println();
}

/**
 * @brief Checks if the current player has won the game.
 * 
 * @return true if the current player has a winning combination, false otherwise.
 */
bool checkWin() {
    for (int i = 0; i < BOARD_SIZE; i++) {
        if (board[i][0] == currentPlayer && board[i][1] == currentPlayer && board[i][2] == currentPlayer) return true;
        if (board[0][i] == currentPlayer && board[1][i] == currentPlayer && board[2][i] == currentPlayer) return true;
    }
    if (board[0][0] == currentPlayer && board[1][1] == currentPlayer && board[2][2] == currentPlayer) return true;
    if (board[0][2] == currentPlayer && board[1][1] == currentPlayer && board[2][0] == currentPlayer) return true;
    return false;
}

/**
 * @brief Checks if the game has ended in a draw.
 * 
 * @return true if the board is full and there is no winner, false otherwise.
 */
bool checkDraw() {
    for (int i = 0; i < BOARD_SIZE; i++) {
        for (int j = 0; j < BOARD_SIZE; j++) {
            if (board[i][j] == ' ') return false;
        }
    }
    return true;
}

/**
 * @brief Performs a random move for the AI.
 * Places the current player's symbol at a random empty position on the board.
 */
void aiMoveRandom() {
    while (true) {
        int row = random(0, BOARD_SIZE);
        int col = random(0, BOARD_SIZE);
        if (board[row][col] == ' ') {
            board[row][col] = currentPlayer;
            break;  // Exit the loop after a valid move
        }
    }
}

/**
 * @brief Handles an AI vs AI game mode, making random moves until the game is over.
 * Alternates moves between two AI players until a win or draw condition is met.
 */
void handleAiVsAi() {
    while (!gameOver) {
        if (checkDraw()) {
            sendJsonMessage("win_status", "It's a draw!");
            gameOver = true;
            return;
        }

        aiMoveRandom();  // AI makes a random move

        if (checkWin()) {
            String message = "Player " + String(currentPlayer) + " wins!";
            sendBoardState(); 
            sendJsonMessage("win_status", message.c_str());
            gameOver = true;
            return;
        }
        currentPlayer = (currentPlayer == 'X') ? 'O' : 'X';  // Switch players
        sendBoardState();  // Send the board state after each move
    }
}

/**
 * @brief Makes a move for the current player at the specified board position.
 * 
 * @param row The row index (0-2).
 * @param col The column index (0-2).
 * @return true if the move is valid and successful, false otherwise.
 */
bool makeMove(int row, int col) {
    if (row >= 0 && row < BOARD_SIZE && col >= 0 && col < BOARD_SIZE && board[row][col] == ' ' && !gameOver) {
        board[row][col] = currentPlayer;
        if (checkWin()) {
            String message = "Player " + String(currentPlayer) + " wins!";
            sendJsonMessage("win_status", message.c_str());
            gameOver = true;
        } else if (checkDraw()) {
            sendJsonMessage("win_status", "It's a draw!");
            gameOver = true;
        } else {
            currentPlayer = (currentPlayer == 'X') ? 'O' : 'X';
        }
        return true;
    }
    return false;
}

/**
 * @brief Initializes the game and sends a startup message.
 * Sets up Serial communication and initializes the board.
 */
void setup() {
    Serial.begin(9600);
    initializeBoard();
    sendJsonMessage("info", "TicTacToe Game Started");
}

/**
 * @brief Main game loop, reads Serial input and processes commands.
 * Processes moves, resets, and mode changes based on JSON commands from Serial input.
 */
void loop() {
    if (Serial.available() > 0) {
        StaticJsonDocument<200> doc;
        String input = Serial.readStringUntil('\n');
        DeserializationError error = deserializeJson(doc, input);

        if (!error) {
            const char* command = doc["command"];
            if (strcmp(command, "MOVE") == 0) {
                int row = doc["row"];
                int col = doc["col"];
                if (makeMove(row, col)) {
                    sendBoardState();
                } else {
                    sendJsonMessage("error", "Invalid move.");
                }
            } else if (strcmp(command, "RESET") == 0) {
                initializeBoard();
                sendJsonMessage("game_status", "Game reset.");
                sendBoardState();
            } else if (strcmp(command, "MODE") == 0) {
                gameMode = doc["mode"];
                String message = "Game mode set to " + String(gameMode);
                sendJsonMessage("game_mode", message.c_str());
                initializeBoard();
                sendJsonMessage("game_status", "Game reset.");
                sendBoardState();
            }

            // AI move logic if applicable
            if (gameMode == 1 && !gameOver && currentPlayer == 'O') {
                aiMoveRandom();  // Make a random move for the AI
                if (checkWin()) {
                    String message = "Player " + String(currentPlayer) + " wins!";
                    sendJsonMessage("win_status", message.c_str());
                    gameOver = true;
                } else if (checkDraw()) {
                    sendJsonMessage("win_status", "It's a draw!");
                    gameOver = true;
                }
                currentPlayer = 'X';  // Switch back to Player X
                sendBoardState();
            } else if (gameMode == 2 && !gameOver) {
                handleAiVsAi();  // Handle AI vs AI
            }
        }
    }
}
