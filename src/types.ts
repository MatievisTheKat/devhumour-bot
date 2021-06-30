export interface Post {
  similar: string[];
  reposts: string[];
}

export interface File {
  [id: string]: Post;
}
