package queue

import (
	"errors"
)

// Message represents an email message to be sent
type Message struct {
	From string
	To   []string
	Data []byte
}

// Queue handles the storage and retrieval of messages using a channel
type Queue struct {
	messages chan Message
}

// NewQueue creates a new Queue
func NewQueue() *Queue {
	return &Queue{
		messages: make(chan Message, 100), // Buffer of 100
	}
}

// Enqueue adds a message to the queue
func (q *Queue) Enqueue(msg *Message) error {
	select {
	case q.messages <- *msg:
		return nil
	default:
		return errors.New("queue is full")
	}
}

// Dequeue returns a message from the queue, blocking until one is available
func (q *Queue) Dequeue() *Message {
	msg := <-q.messages
	return &msg
}
