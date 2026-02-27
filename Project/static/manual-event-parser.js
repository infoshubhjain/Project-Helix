// ** MANUAL EVENT PARSER ** //
// Intelligent event extraction from natural language text

class ManualEventParser {
    constructor() {
        this.monthNames = [
            'january', 'february', 'march', 'april', 'may', 'june',
            'july', 'august', 'september', 'october', 'november', 'december'
        ];
        
        this.monthAbbrevs = [
            'jan', 'feb', 'mar', 'apr', 'may', 'jun',
            'jul', 'aug', 'sep', 'oct', 'nov', 'dec'
        ];
        
        this.weekdays = [
            'sunday', 'monday', 'tuesday', 'wednesday', 'thursday', 'friday', 'saturday'
        ];
        
        this.weekdayAbbrevs = ['sun', 'mon', 'tue', 'wed', 'thu', 'fri', 'sat'];
        
        this.uiucLocations = {
            'engineering building': { building: 'Engineering Hall', campus: 'Urbana' },
            'eb': { building: 'Engineering Hall', campus: 'Urbana' },
            'siebel center': { building: 'Siebel Center for Design', campus: 'Urbana' },
            'siebel': { building: 'Siebel Center for Design', campus: 'Urbana' },
            'grainger library': { building: 'Grainger Engineering Library', campus: 'Urbana' },
            'undergrad library': { building: 'Undergraduate Library', campus: 'Urbana' },
            'ugl': { building: 'Undergraduate Library', campus: 'Urbana' },
            'main library': { building: 'Main Library', campus: 'Urbana' },
            'union': { building: 'Illinois Union', campus: 'Urbana' },
            'student union': { building: 'Illinois Union', campus: 'Urbana' },
            'arc': { building: 'Activities and Recreation Center', campus: 'Urbana' },
            'crce': { building: 'Campus Recreation Center East', campus: 'Urbana' },
            'state farm center': { building: 'State Farm Center', campus: 'Champaign' },
            'memorial stadium': { building: 'Memorial Stadium', campus: 'Champaign' },
            'assembly hall': { building: 'State Farm Center', campus: 'Champaign' }, // Historic name
            'nrc': { building: 'Natural Resources Building', campus: 'Urbana' },
            'lincoln hall': { building: 'Lincoln Hall', campus: 'Urbana' },
            'gregory hall': { building: 'Gregory Hall', campus: 'Urbana' },
            'english building': { building: 'English Building', campus: 'Urbana' },
            'business building': { building: 'Business Instructional Facility', campus: 'Urbana' },
            'bif': { building: 'Business Instructional Facility', campus: 'Urbana' }
        };
        
        this.timePatterns = [
            // 12-hour format with AM/PM
            /(\d{1,2}):(\d{2})\s*(am|pm)/gi,
            // 12-hour format without minutes
            /(\d{1,2})\s*(am|pm)/gi,
            // 24-hour format
            /(\d{1,2}):(\d{2})\s*(?:hours?|hrs?)/gi,
            // Time ranges
            /(\d{1,2}):?(\d{0,2})?\s*(am|pm)?\s*[-–]\s*(\d{1,2}):?(\d{0,2})?\s*(am|pm)?/gi
        ];
        
        this.datePatterns = [
            // Month Day, Year
            /(january|february|march|april|may|june|july|august|september|october|november|december|jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)\s+(\d{1,2})(?:st|nd|rd|th)?,?\s*(\d{4})?/gi,
            // Day Month, Year
            /(\d{1,2})(?:st|nd|rd|th)?\s+(january|february|march|april|may|june|july|august|september|october|november|december|jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec),?\s*(\d{4})?/gi,
            // Weekday relative dates
            /(sunday|monday|tuesday|wednesday|thursday|friday|saturday|sun|mon|tue|wed|thu|fri|sat)/gi,
            // Today, tomorrow, yesterday
            /(today|tomorrow|yesterday)/gi,
            // Next/last weekday
            /(next|last)\s+(sunday|monday|tuesday|wednesday|thursday|friday|saturday|sun|mon|tue|wed|thu|fri|sat)/gi
        ];
    }
    
    parseEvents(text, options = {}) {
        const events = [];
        const currentYear = new Date().getFullYear();
        
        // Split text by common event separators
        const eventSentences = this.splitIntoEvents(text);
        
        for (const sentence of eventSentences) {
            if (sentence.trim().length < 10) continue; // Skip very short sentences
            
            const event = this.extractEventFromSentence(sentence, currentYear, options);
            if (event && this.isValidEvent(event)) {
                events.push(event);
            }
        }
        
        return events;
    }
    
    splitIntoEvents(text) {
        // Split by common sentence separators and newlines
        return text.split(/[\.\n]+/).filter(s => s.trim().length > 0);
    }
    
    extractEventFromSentence(sentence, currentYear, options) {
        const event = {
            title: '',
            description: sentence.trim(),
            location: '',
            start: null,
            end: null,
            confidence: 0
        };
        
        // Extract date/time information
        const dateInfo = this.extractDateTime(sentence, currentYear);
        if (!dateInfo.hasDateTime) {
            return null; // Skip if no date/time found
        }
        
        event.start = dateInfo.start;
        event.end = dateInfo.end;
        
        // Extract location
        if (options.autoDetectLocation) {
            event.location = this.extractLocation(sentence);
        }
        
        // Extract title (first part before time/date info)
        event.title = this.extractTitle(sentence, dateInfo);
        
        // Calculate confidence score
        event.confidence = this.calculateConfidence(event, dateInfo);
        
        return event;
    }
    
    extractDateTime(sentence, currentYear) {
        const result = {
            hasDateTime: false,
            start: null,
            end: null,
            dateFound: null,
            timeFound: null
        };
        
        // Extract date
        let dateMatch = null;
        for (const pattern of this.datePatterns) {
            const matches = [...sentence.matchAll(pattern)];
            if (matches.length > 0) {
                dateMatch = matches[0];
                break;
            }
        }
        
        // Extract time
        let timeMatch = null;
        for (const pattern of this.timePatterns) {
            const matches = [...sentence.matchAll(pattern)];
            if (matches.length > 0) {
                timeMatch = matches[0];
                break;
            }
        }
        
        if (!dateMatch && !timeMatch) {
            return result;
        }
        
        result.hasDateTime = true;
        
        // Parse date
        let eventDate = new Date(); // Default to today
        
        if (dateMatch) {
            eventDate = this.parseDate(dateMatch, currentYear);
            result.dateFound = dateMatch[0];
        }
        
        // Parse time
        if (timeMatch) {
            const timeInfo = this.parseTime(timeMatch, eventDate);
            result.start = timeInfo.start;
            result.end = timeInfo.end;
            result.timeFound = timeMatch[0];
        } else {
            // Default time if no time specified
            result.start = new Date(eventDate);
            result.start.setHours(12, 0, 0, 0); // Default to noon
            result.end = new Date(result.start);
            result.end.setHours(result.start.getHours() + 1); // 1 hour default
        }
        
        return result;
    }
    
    parseDate(match, currentYear) {
        const [, monthOrDay, dayOrMonth, year] = match;
        
        // Check if it's a weekday
        if (this.weekdays.includes(monthOrDay.toLowerCase()) || this.weekdayAbbrevs.includes(monthOrDay.toLowerCase())) {
            return this.parseRelativeDate(monthOrDay.toLowerCase());
        }
        
        // Check if it's today/tomorrow/yesterday
        const relativeDay = monthOrDay.toLowerCase();
        if (relativeDay === 'today') return new Date();
        if (relativeDay === 'tomorrow') {
            const tomorrow = new Date();
            tomorrow.setDate(tomorrow.getDate() + 1);
            return tomorrow;
        }
        if (relativeDay === 'yesterday') {
            const yesterday = new Date();
            yesterday.setDate(yesterday.getDate() - 1);
            return yesterday;
        }
        
        // Parse month/day format
        let month, day, yearToUse = year || currentYear.toString();
        
        // Check if first group is month name
        if (this.monthNames.includes(monthOrDay.toLowerCase()) || this.monthAbbrevs.includes(monthOrDay.toLowerCase())) {
            month = this.getMonthNumber(monthOrDay);
            day = parseInt(dayOrMonth);
        } else {
            // First group is day, second is month
            day = parseInt(monthOrDay);
            month = this.getMonthNumber(dayOrMonth);
        }
        
        return new Date(yearToUse, month - 1, day);
    }
    
    parseRelativeDate(weekday) {
        const today = new Date();
        const currentDay = today.getDay();
        const targetDay = this.getWeekdayNumber(weekday);
        
        let daysToAdd = targetDay - currentDay;
        if (daysToAdd <= 0) {
            daysToAdd += 7; // Next occurrence
        }
        
        const result = new Date(today);
        result.setDate(result.getDate() + daysToAdd);
        return result;
    }
    
    parseTime(match, eventDate) {
        const result = { start: null, end: null };
        
        // Check if it's a time range
        if (match[0].includes('-') || match[0].includes('–')) {
            return this.parseTimeRange(match, eventDate);
        }
        
        // Single time
        let hours, minutes, meridiem;
        
        if (match.length >= 4) {
            // Format with minutes: HH:MM AM/PM
            [, hours, minutes, meridiem] = match;
        } else {
            // Format without minutes: H AM/PM
            [, hours, meridiem] = match;
            minutes = '0';
        }
        
        hours = parseInt(hours);
        minutes = parseInt(minutes || '0');
        
        // Convert to 24-hour format
        if (meridiem) {
            meridiem = meridiem.toLowerCase();
            if (meridiem === 'pm' && hours !== 12) hours += 12;
            if (meridiem === 'am' && hours === 12) hours = 0;
        }
        
        result.start = new Date(eventDate);
        result.start.setHours(hours, minutes, 0, 0);
        
        result.end = new Date(result.start);
        result.end.setHours(result.start.getHours() + 1); // 1 hour default
        
        return result;
    }
    
    parseTimeRange(match, eventDate) {
        const result = { start: null, end: null };
        
        // Extract start and end times
        const rangeMatch = match[0].match(/(\d{1,2}):?(\d{0,2})?\s*(am|pm)?\s*[-–]\s*(\d{1,2}):?(\d{0,2})?\s*(am|pm)?/i);
        
        if (!rangeMatch) {
            return this.parseTime(match, eventDate); // Fallback to single time parsing
        }
        
        const [, startHours, startMinutes, startMeridiem, endHours, endMinutes, endMeridiem] = rangeMatch;
        
        // Parse start time
        let sh = parseInt(startHours);
        let sm = parseInt(startMinutes || '0');
        if (startMeridiem) {
            if (startMeridiem.toLowerCase() === 'pm' && sh !== 12) sh += 12;
            if (startMeridiem.toLowerCase() === 'am' && sh === 12) sh = 0;
        }
        
        // Parse end time
        let eh = parseInt(endHours);
        let em = parseInt(endMinutes || '0');
        if (endMeridiem) {
            if (endMeridiem.toLowerCase() === 'pm' && eh !== 12) eh += 12;
            if (endMeridiem.toLowerCase() === 'am' && eh === 12) eh = 0;
        } else if (startMeridiem) {
            // Inherit meridiem if not specified for end time
            if (startMeridiem.toLowerCase() === 'pm' && eh !== 12) eh += 12;
            if (startMeridiem.toLowerCase() === 'am' && eh === 12) eh = 0;
        }
        
        result.start = new Date(eventDate);
        result.start.setHours(sh, sm, 0, 0);
        
        result.end = new Date(eventDate);
        result.end.setHours(eh, em, 0, 0);
        
        // Handle cross-midnight events
        if (result.end < result.start) {
            result.end.setDate(result.end.getDate() + 1);
        }
        
        return result;
    }
    
    extractLocation(sentence) {
        const lowerSentence = sentence.toLowerCase();
        
        // Check for UIUC locations first
        for (const [key, location] of Object.entries(this.uiucLocations)) {
            if (lowerSentence.includes(key)) {
                let locationText = location.building;
                
                // Extract room number if present
                const roomMatch = sentence.match(/room\s+(\w+\d*\w*)/i);
                if (roomMatch) {
                    locationText += `, Room ${roomMatch[1]}`;
                }
                
                return locationText;
            }
        }
        
        // Generic location patterns
        const locationPatterns = [
            /(?:in|at|@)\s+([^,.!?]+?)(?:\s+(?:for|to|with|and|on|at|in)|[,.!?])/gi,
            /(?:room|building|hall|center)\s+([^,.!?]+)/gi
        ];
        
        for (const pattern of locationPatterns) {
            const matches = [...sentence.matchAll(pattern)];
            if (matches.length > 0) {
                return matches[0][1].trim();
            }
        }
        
        return '';
    }
    
    extractTitle(sentence, dateInfo) {
        // Remove date/time information from title
        let title = sentence.trim();
        
        // Remove found date and time patterns
        if (dateInfo.dateFound) {
            title = title.replace(dateInfo.dateFound, '');
        }
        if (dateInfo.timeFound) {
            title = title.replace(dateInfo.timeFound, '');
        }
        
        // Remove common location indicators
        title = title.replace(/\b(in|at|@)\s+[^,.!?]+/gi, '');
        
        // Clean up extra spaces and punctuation
        title = title.replace(/\s+/g, ' ').trim();
        title = title.replace(/^[,\.\s]+|[,\.\s]+$/g, '');
        
        // If title is too short, use the first part of the original sentence
        if (title.length < 5) {
            const words = sentence.trim().split(/\s+/);
            title = words.slice(0, 5).join(' ');
        }
        
        return title;
    }
    
    calculateConfidence(event, dateInfo) {
        let confidence = 0;
        
        // Base confidence for having date/time
        if (dateInfo.hasDateTime) confidence += 40;
        
        // Bonus for specific date
        if (dateInfo.dateFound) confidence += 20;
        
        // Bonus for specific time
        if (dateInfo.timeFound) confidence += 20;
        
        // Bonus for location
        if (event.location) confidence += 15;
        
        // Bonus for reasonable title length
        if (event.title && event.title.length > 5 && event.title.length < 100) confidence += 5;
        
        return Math.min(confidence, 100);
    }
    
    isValidEvent(event) {
        return event.title && event.start && event.confidence > 30;
    }
    
    getMonthNumber(monthStr) {
        monthStr = monthStr.toLowerCase();
        
        for (let i = 0; i < this.monthNames.length; i++) {
            if (this.monthNames[i].startsWith(monthStr) || this.monthAbbrevs[i].startsWith(monthStr)) {
                return i + 1;
            }
        }
        
        return 1; // Default to January
    }
    
    getWeekdayNumber(weekday) {
        weekday = weekday.toLowerCase();
        
        for (let i = 0; i < this.weekdays.length; i++) {
            if (this.weekdays[i].startsWith(weekday) || this.weekdayAbbrevs[i].startsWith(weekday)) {
                return i;
            }
        }
        
        return 0; // Default to Sunday
    }
}

// Make available globally
window.ManualEventParser = ManualEventParser;
