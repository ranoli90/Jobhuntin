import React from "react";

interface AuthorProperties {
  author: {
    id: string;
    name: string;
    title: string;
    bio: string;
    image: string;
    social: {
      twitter: string;
      linkedin: string;
    };
  };
}

const Author: React.FC<AuthorProperties> = ({ author }) => {
  if (!author) {
    return null;
  }

  return (
    <div className="bg-slate-100 p-6 rounded-lg my-8 flex items-center">
      <img
        src={author.image}
        alt={author.name}
        className="w-24 h-24 rounded-full mr-6"
      />
      <div>
        <h3 className="text-xl font-bold mb-2">{author.name}</h3>
        <p className="text-slate-600 mb-2">{author.title}</p>
        <p className="text-slate-600 mb-4">{author.bio}</p>
        <div className="flex gap-4">
          <a
            href={author.social.twitter}
            target="_blank"
            rel="noreferrer"
            className="text-slate-600 hover:text-slate-900"
          >
            Twitter
          </a>
          <a
            href={author.social.linkedin}
            target="_blank"
            rel="noreferrer"
            className="text-slate-600 hover:text-slate-900"
          >
            LinkedIn
          </a>
        </div>
      </div>
    </div>
  );
};

export default Author;
