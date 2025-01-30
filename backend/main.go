package main

import (
	"context"
	"fmt"
	"log"
	"net/http"
	"os"
	"path/filepath"

	"github.com/gin-gonic/gin"
	"github.com/joho/godotenv"
	openai "github.com/sashabaranov/go-openai"
)

type Config struct {
	OpenAIKey string
	Port      string
}

type Server struct {
	config       Config
	openaiClient *openai.Client
}

func NewServer(config Config) *Server {
	return &Server{
		config:       config,
		openaiClient: openai.NewClient(config.OpenAIKey),
	}
}

func (s *Server) handleUpdateOpenAIKey(c *gin.Context) {
	var req struct {
		Key string `json:"key" binding:"required"`
	}

	if err := c.ShouldBindJSON(&req); err != nil {
		c.JSON(http.StatusBadRequest, gin.H{"error": err.Error()})
		return
	}

	// 更新 OpenAI client
	s.openaiClient = openai.NewClient(req.Key)
	s.config.OpenAIKey = req.Key

	c.JSON(http.StatusOK, gin.H{"message": "API key updated successfully"})
}

func (s *Server) handleUploadPDF(c *gin.Context) {
	file, err := c.FormFile("file")
	if err != nil {
		c.JSON(http.StatusBadRequest, gin.H{"error": "No file uploaded"})
		return
	}

	// 確保檔案是 PDF
	if filepath.Ext(file.Filename) != ".pdf" {
		c.JSON(http.StatusBadRequest, gin.H{"error": "File must be a PDF"})
		return
	}

	// 建立上傳目錄
	uploadDir := "./uploads"
	if err := os.MkdirAll(uploadDir, 0755); err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{"error": "Failed to create upload directory"})
		return
	}

	filename := filepath.Join(uploadDir, file.Filename)
	if err := c.SaveUploadedFile(file, filename); err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{"error": "Failed to save file"})
		return
	}

	c.JSON(http.StatusOK, gin.H{
		"message":  "File uploaded successfully",
		"filename": file.Filename,
	})
}

func (s *Server) handleAnalyzeQuery(c *gin.Context) {
	var req struct {
		Query    string `json:"query" binding:"required"`
		Filename string `json:"filename" binding:"required"`
	}

	if err := c.ShouldBindJSON(&req); err != nil {
		c.JSON(http.StatusBadRequest, gin.H{"error": err.Error()})
		return
	}

	// 檢查檔案是否存在
	filename := filepath.Join("./uploads", req.Filename)
	if _, err := os.Stat(filename); os.IsNotExist(err) {
		c.JSON(http.StatusNotFound, gin.H{"error": "File not found"})
		return
	}

	// 使用 OpenAI API 進行分析
	resp, err := s.openaiClient.CreateChatCompletion(
		context.Background(),
		openai.ChatCompletionRequest{
			Model: openai.GPT4,
			Messages: []openai.ChatCompletionMessage{
				{
					Role:    openai.ChatMessageRoleSystem,
					Content: "You are a threat intelligence analyst. Analyze the provided information and extract relevant IoCs and threat intelligence details.",
				},
				{
					Role:    openai.ChatMessageRoleUser,
					Content: fmt.Sprintf("Regarding the threat intelligence report in %s, %s", req.Filename, req.Query),
				},
			},
		},
	)

	if err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{"error": err.Error()})
		return
	}

	c.JSON(http.StatusOK, gin.H{
		"response": resp.Choices[0].Message.Content,
	})
}

func main() {
	// 載入環境變數
	if err := godotenv.Load(); err != nil {
		log.Printf("Warning: .env file not found")
	}

	config := Config{
		OpenAIKey: os.Getenv("OPENAI_API_KEY"),
		Port:      os.Getenv("PORT"),
	}

	if config.Port == "" {
		config.Port = "8080"
	}

	server := NewServer(config)
	router := gin.Default()

	// CORS 設定
	router.Use(func(c *gin.Context) {
		c.Writer.Header().Set("Access-Control-Allow-Origin", "*")
		c.Writer.Header().Set("Access-Control-Allow-Methods", "POST, GET, OPTIONS, PUT, DELETE")
		c.Writer.Header().Set("Access-Control-Allow-Headers", "Content-Type, Content-Length, Accept-Encoding, Authorization")
		if c.Request.Method == "OPTIONS" {
			c.AbortWithStatus(204)
			return
		}
		c.Next()
	})

	// API 路由
	router.POST("/api/key", server.handleUpdateOpenAIKey)
	router.POST("/api/upload", server.handleUploadPDF)
	router.POST("/api/analyze", server.handleAnalyzeQuery)

	// 啟動服務器
	log.Printf("Server starting on port %s", config.Port)
	if err := router.Run(":" + config.Port); err != nil {
		log.Fatal(err)
	}
}
