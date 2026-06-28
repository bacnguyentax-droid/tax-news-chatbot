import { getNews } from '@/lib/db';
import NewsFeed from '@/components/NewsFeed';

// Enable dynamic rendering since database updates can occur dynamically in the admin panel
export const dynamic = 'force-dynamic';

export default function Home() {
  const newsList = getNews();

  return (
    <div style={{ paddingBottom: '60px' }}>
      <NewsFeed initialNews={newsList} />
    </div>
  );
}
