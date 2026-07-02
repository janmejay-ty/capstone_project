import ReactMarkdown from 'react-markdown'
import remarkGfm from 'remark-gfm'

interface MarkdownRendererProps {
  content: string;
  isUser: boolean;
}

const getMarkdownComponents = (isUser: boolean) => ({
  h1: ({ children, ...props }: any) => <h1 className={`text-xl font-bold mt-4 mb-2 ${isUser ? 'text-white' : 'text-purple-400'}`} {...props}>{children}</h1>,
  h2: ({ children, ...props }: any) => <h2 className={`text-lg font-bold mt-3 mb-2 ${isUser ? 'text-white' : 'text-purple-400'}`} {...props}>{children}</h2>,
  h3: ({ children, ...props }: any) => <h3 className={`text-base font-bold mt-2 mb-1 ${isUser ? 'text-white' : 'text-purple-400'}`} {...props}>{children}</h3>,
  p: ({ children, ...props }: any) => <p className="mb-2 leading-relaxed last:mb-0" {...props}>{children}</p>,
  ul: ({ children, ...props }: any) => <ul className="list-disc pl-5 mb-2 space-y-1" {...props}>{children}</ul>,
  ol: ({ children, ...props }: any) => <ol className="list-decimal pl-5 mb-2 space-y-1" {...props}>{children}</ol>,
  li: ({ children, ...props }: any) => <li className="mb-0.5" {...props}>{children}</li>,
  code: ({ className, children, ...props }: any) => {
    const match = /language-(\w+)/.exec(className || '');
    return match ? (
      <pre className={`border rounded-lg p-3 overflow-x-auto my-2 font-mono text-xs ${isUser ? 'bg-purple-800 border-purple-500 text-purple-100' : 'bg-purple-950/30 border-purple-800/20 text-purple-200'}`}>
        <code className={className} {...props}>
          {children}
        </code>
      </pre>
    ) : (
      <code className={`px-1 py-0.5 rounded text-xs font-mono border ${isUser ? 'bg-purple-800 border-purple-500 text-purple-100' : 'bg-purple-950/40 border-purple-800/30 text-purple-300'}`} {...props}>
        {children}
      </code>
    );
  },
  a: ({ children, ...props }: any) => <a className={`${isUser ? 'text-white hover:text-purple-200 underline' : 'text-purple-400 hover:text-purple-300 underline'} transition-all`} {...props}>{children}</a>,
  blockquote: ({ children, ...props }: any) => <blockquote className={`border-l-4 pl-4 py-1 my-2 rounded-r ${isUser ? 'border-white bg-white/10' : 'border-purple-500 bg-purple-500/5'}`} {...props}>{children}</blockquote>,
  table: ({ children, ...props }: any) => <div className="overflow-x-auto my-3"><table className={`min-w-full divide-y border rounded-lg overflow-hidden text-xs ${isUser ? 'divide-purple-500 border-purple-500' : 'divide-card-border border-card-border'}`} {...props}>{children}</table></div>,
  thead: ({ children, ...props }: any) => <thead className={isUser ? 'bg-purple-700 text-white' : 'bg-pill-bg text-pill-text'} {...props}>{children}</thead>,
  tbody: ({ children, ...props }: any) => <tbody className={isUser ? 'divide-y divide-purple-500' : 'divide-y divide-card-border'} {...props}>{children}</tbody>,
  tr: ({ children, ...props }: any) => <tr className={isUser ? 'hover:bg-purple-500/25 transition-all' : 'hover:bg-hover/20 transition-all'} {...props}>{children}</tr>,
  th: ({ children, ...props }: any) => <th className="px-3 py-2 text-left font-semibold" {...props}>{children}</th>,
  td: ({ children, ...props }: any) => <td className="px-3 py-2" {...props}>{children}</td>,
});

export default function MarkdownRenderer({ content, isUser }: MarkdownRendererProps) {
  return (
    <div className="text-sm leading-relaxed">
      <ReactMarkdown 
        remarkPlugins={[remarkGfm]} 
        components={getMarkdownComponents(isUser)}
      >
        {content}
      </ReactMarkdown>
    </div>
  );
}
