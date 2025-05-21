import { Link } from 'react-router-dom';

/**
 * 404 Not Found page
 */
const NotFoundPage = () => {
  return (
    <div className="not-found-page">
      <h1>404 - Page Not Found</h1>
      <p>
        The page you are looking for does not exist or has been moved.
      </p>
      <Link to="/" className="home-link">
        Return to Home
      </Link>
    </div>
  );
};

export default NotFoundPage; 