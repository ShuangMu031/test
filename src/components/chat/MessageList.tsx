import React from 'react';
import { Message } from '../../store/chatStore';
import MessageBubble from './MessageBubble';

interface MessageListProps {
  messages: Message[];
}

const MessageList: React.FC<MessageListProps> = ({ messages }) => {
  return (
    <div className="flex-1 overflow-y-auto p-4 space-y-4">
      {messages.map((message, index) => (
        <MessageBubble
          key={index}
          content={message.content}
          isUser={message.isUser}
          timestamp={message.timestamp}
          emotion={message.emotion}
        />
      ))}
    </div>
  );
};

export default MessageList;