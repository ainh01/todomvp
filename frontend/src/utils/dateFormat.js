/**
 * Date formatting utilities using date-fns
 */

import { formatDistanceToNow, format, parseISO } from 'date-fns';

/**
 * Format ISO timestamp to relative time (e.g., "2 hours ago")
 */
export const formatRelativeTime = (isoTimestamp) => {
  if (!isoTimestamp) return '';
  
  try {
    const date = parseISO(isoTimestamp);
    return formatDistanceToNow(date, { addSuffix: true });
  } catch (error) {
    console.error('Error formatting date:', error);
    return isoTimestamp;
  }
};

/**
 * Format ISO timestamp to readable date (e.g., "Jan 15, 2024 10:30 AM")
 */
export const formatReadableDate = (isoTimestamp) => {
  if (!isoTimestamp) return '';
  
  try {
    const date = parseISO(isoTimestamp);
    return format(date, 'MMM dd, yyyy h:mm a');
  } catch (error) {
    console.error('Error formatting date:', error);
    return isoTimestamp;
  }
};
