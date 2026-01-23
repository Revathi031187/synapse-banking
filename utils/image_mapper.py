"""
Image Mapper Service for Academy Sports Personas

Maps persona characteristics to appropriate lifestyle images.
Uses curated Unsplash URLs and fallback to local assets.
"""

from typing import Dict, List, Optional
import hashlib


class ImageMapper:
    """
    Maps personas to lifestyle images based on characteristics
    """
    
    # Curated Unsplash images for macro personas (multiple per category for variety)
    MACRO_PERSONA_IMAGES = {
        'fishing': [
            {'url': 'https://images.unsplash.com/photo-1559827260-dc66d52bef19?w=800&q=80', 'color_theme': '#1e40af'},
            {'url': 'https://images.unsplash.com/photo-1544552866-d3ed42536cfd?w=800&q=80', 'color_theme': '#0c4a6e'},
            {'url': 'https://images.unsplash.com/photo-1498654077810-12c21d4d6dc3?w=800&q=80', 'color_theme': '#164e63'}
        ],
        'camping': [
            {'url': 'https://images.unsplash.com/photo-1478131143081-80f7f84ca84d?w=800&q=80', 'color_theme': '#c44536'},
            {'url': 'https://images.unsplash.com/photo-1504280390367-361c6d9f38f4?w=800&q=80', 'color_theme': '#dc2626'},
            {'url': 'https://images.unsplash.com/photo-1445308394109-4ec2920981b1?w=800&q=80', 'color_theme': '#b91c1c'}
        ],
        'hiking': [
            {'url': 'https://images.unsplash.com/photo-1551632811-561732d1e306?w=800&q=80', 'color_theme': '#16a34a'},
            {'url': 'https://images.unsplash.com/photo-1445308394109-4ec2920981b1?w=800&q=80', 'color_theme': '#15803d'},
            {'url': 'https://images.unsplash.com/photo-1464822759023-fed622ff2c3b?w=800&q=80', 'color_theme': '#166534'},
            {'url': 'https://images.unsplash.com/photo-1682687220742-aba13b6e50ba?w=800&q=80', 'color_theme': '#14532d'}
        ],
        'backpack': [
            {'url': 'https://images.unsplash.com/photo-1622260614153-03223fb72052?w=800&q=80', 'color_theme': '#2563eb'},
            {'url': 'https://images.unsplash.com/photo-1551632811-561732d1e306?w=800&q=80', 'color_theme': '#1d4ed8'},
            {'url': 'https://images.unsplash.com/photo-1473773508845-188df298d2d1?w=800&q=80', 'color_theme': '#1e40af'}
        ],
        'family': [
            {'url': 'https://images.unsplash.com/photo-1523987355523-c7b5b0dd90a7?w=800&q=80', 'color_theme': '#d97706'},
            {'url': 'https://images.unsplash.com/photo-1537905569824-f89f14cceb68?w=800&q=80', 'color_theme': '#ea580c'},
            {'url': 'https://images.unsplash.com/photo-1478131143081-80f7f84ca84d?w=800&q=80', 'color_theme': '#c2410c'}
        ],
        'shopping': [
            {'url': 'https://images.unsplash.com/photo-1483985988355-763728e1935b?w=800&q=80', 'color_theme': '#7c3aed'},
            {'url': 'https://images.unsplash.com/photo-1472851294608-062f824d29cc?w=800&q=80', 'color_theme': '#6d28d9'},
            {'url': 'https://images.unsplash.com/photo-1607083206968-13611e3d76db?w=800&q=80', 'color_theme': '#5b21b6'}
        ],
        'technical': [
            {'url': 'https://images.unsplash.com/photo-1476610182048-b716b8518aae?w=800&q=80', 'color_theme': '#0891b2'},
            {'url': 'https://images.unsplash.com/photo-1682687220742-aba13b6e50ba?w=800&q=80', 'color_theme': '#0e7490'},
            {'url': 'https://images.unsplash.com/photo-1464822759023-fed622ff2c3b?w=800&q=80', 'color_theme': '#155e75'}
        ],
        'outdoor': [
            {'url': 'https://images.unsplash.com/photo-1504280390367-361c6d9f38f4?w=800&q=80', 'color_theme': '#059669'},
            {'url': 'https://images.unsplash.com/photo-1478131143081-80f7f84ca84d?w=800&q=80', 'color_theme': '#047857'},
            {'url': 'https://images.unsplash.com/photo-1445308394109-4ec2920981b1?w=800&q=80', 'color_theme': '#065f46'}
        ],
        'budget': [
            {'url': 'https://images.unsplash.com/photo-1483985988355-763728e1935b?w=800&q=80', 'color_theme': '#9333ea'},
            {'url': 'https://images.unsplash.com/photo-1472851294608-062f824d29cc?w=800&q=80', 'color_theme': '#7e22ce'},
            {'url': 'https://images.unsplash.com/photo-1607083206968-13611e3d76db?w=800&q=80', 'color_theme': '#6b21a8'}
        ],
        'expert': [
            {'url': 'https://images.unsplash.com/photo-1476610182048-b716b8518aae?w=800&q=80', 'color_theme': '#0284c7'},
            {'url': 'https://images.unsplash.com/photo-1682687220742-aba13b6e50ba?w=800&q=80', 'color_theme': '#0369a1'},
            {'url': 'https://images.unsplash.com/photo-1559827260-dc66d52bef19?w=800&q=80', 'color_theme': '#075985'}
        ]
    }
    
    # Icon mapping for micro segments
    MICRO_SEGMENT_ICONS = {
        'brand_loyalist': '❤️',
        'technical_expert': '⚙️',
        'frequent_buyer': '⭐',
        'bundle_focused': '🎁',
        'category_explorer': '🗺️',
        'value_hunter': '🏷️',
        'selective_shopper': '🎯',
        
        # Traits
        'high_loyalty': '❤️',
        'advanced_expertise': '🎓',
        'high_value': '💎',
        'frequent': '🔄',
        'premium': '👑'
    }
    
    def __init__(self):
        """Initialize image mapper"""
        self.cache = {}
    
    def get_macro_persona_image(
        self,
        persona_name: str,
        characteristics: Dict,
        size: int = 0,
        avg_spend: float = 0.0,
        used_images: set = None
    ) -> Dict:
        """
        Get image and styling for a macro persona with variety (no repeats)
        
        Args:
            persona_name: Name of the persona
            characteristics: Persona characteristics
            size: Number of customers
            avg_spend: Average spend per customer
            used_images: Set of already used image URLs to avoid repeats
            
        Returns:
            Dictionary with image_url, color_theme, emoji
        """
        if used_images is None:
            used_images = set()
        # Determine category based on name and characteristics
        persona_lower = persona_name.lower()
        
        # Match persona to image category (prioritize most specific first)
        if any(word in persona_lower for word in ['backpack', 'pack']):
            category = 'backpack'
            emoji = '🎒'
        elif any(word in persona_lower for word in ['angl', 'fish', 'water', 'boat']):
            category = 'fishing'
            emoji = '🎣'
        elif any(word in persona_lower for word in ['camp', 'tent']):
            category = 'camping'
            emoji = '🏕️'
        elif any(word in persona_lower for word in ['hik', 'trail', 'mountain']):
            category = 'hiking'
            emoji = '⛰️'
        elif any(word in persona_lower for word in ['family', 'adventure', 'group', 'social']):
            category = 'family'
            emoji = '👨‍👩‍👧‍👦'
        elif any(word in persona_lower for word in ['bargain', 'budget', 'value', 'deal', 'price', 'conscious']):
            category = 'budget'
            emoji = '🏷️'
        elif any(word in persona_lower for word in ['expert', 'technical', 'pro', 'specialist', 'quality']):
            category = 'expert'
            emoji = '🎯'
        elif any(word in persona_lower for word in ['casual', 'occasional', 'weekend']):
            category = 'outdoor'
            emoji = '🏕️'
        elif any(word in persona_lower for word in ['beginner', 'new', 'starter']):
            category = 'outdoor'
            emoji = '⛺'
        elif any(word in persona_lower for word in ['intermediate', 'mid']):
            category = 'hiking'
            emoji = '⛰️'
        else:
            # Default to outdoor for general sports
            category = 'outdoor'
            emoji = '🏕️'
        
        # Get image variants for this category
        image_variants = self.MACRO_PERSONA_IMAGES.get(category, self.MACRO_PERSONA_IMAGES['outdoor'])
        
        # Use MD5 hash for better distribution and uniqueness
        # This ensures different personas get different images even in same category
        name_hash = hashlib.md5(persona_name.encode()).hexdigest()
        # Use first 8 hex chars converted to int for better distribution
        image_index = int(name_hash[:8], 16) % len(image_variants)
        selected_image = image_variants[image_index]
        
        # Ensure no image repeats if used_images is provided
        attempts = 0
        while selected_image['url'] in used_images and attempts < len(image_variants):
            image_index = (image_index + 1) % len(image_variants)
            selected_image = image_variants[image_index]
            attempts += 1
        
        # Add to used images set
        used_images.add(selected_image['url'])
        
        # Use fallback as the next image in rotation
        fallback_index = (image_index + 1) % len(image_variants)
        fallback_image = image_variants[fallback_index]
        
        return {
            'image_url': selected_image['url'],
            'image_fallback': fallback_image['url'],
            'color_theme': selected_image['color_theme'],
            'emoji': emoji,
            'keywords': [category]
        }
    
    def get_micro_segment_icons(
        self,
        segment_name: str,
        characteristics: Dict
    ) -> List[str]:
        """
        Get icons for a micro segment based on characteristics
        
        Args:
            segment_name: Name of the micro segment
            characteristics: Segment characteristics
            
        Returns:
            List of emoji icons
        """
        icons = []
        name_lower = segment_name.lower()
        
        # Primary icon based on name
        if 'loyalist' in name_lower or 'loyal' in name_lower:
            icons.append('❤️')
        elif 'expert' in name_lower or 'technical' in name_lower:
            icons.append('⚙️')
        elif 'frequent' in name_lower or 'buyer' in name_lower:
            icons.append('⭐')
        elif 'bundle' in name_lower:
            icons.append('🎁')
        elif 'explorer' in name_lower or 'category' in name_lower:
            icons.append('🗺️')
        elif 'value' in name_lower or 'hunter' in name_lower:
            icons.append('🏷️')
        else:
            icons.append('🎯')
        
        # Add tier icon based on characteristics
        avg_ltv = characteristics.get('avg_ltv', 0)
        if avg_ltv > 2000:
            icons.append('👑')  # Premium
        elif avg_ltv > 1500:
            icons.append('💎')  # High value
        
        # Add loyalty icon
        brand_loyalty = characteristics.get('avg_brand_loyalty', 0)
        if brand_loyalty > 0.7 and '❤️' not in icons:
            icons.append('❤️')
        
        return icons[:3]  # Max 3 icons
    
    def get_trait_badges(
        self,
        characteristics: Dict,
        ltv_tier: str
    ) -> List[Dict]:
        """
        Generate trait badges for micro segment display
        
        Args:
            characteristics: Segment characteristics
            ltv_tier: LTV tier (Bronze/Silver/Gold/Platinum)
            
        Returns:
            List of badge dictionaries with label and value
        """
        badges = []
        
        # Loyalty badge
        brand_loyalty = characteristics.get('avg_brand_loyalty', 0)
        if brand_loyalty > 0.7:
            badges.append({
                'icon': '❤️',
                'label': 'High Loyalty',
                'color': 'red'
            })
        
        # Expertise badge
        expertise = characteristics.get('avg_expertise', 0)
        if expertise > 4.0:
            level = 'Advanced'
        elif expertise > 3.0:
            level = 'Intermediate'
        else:
            level = 'Beginner'
        
        badges.append({
            'icon': '🎓',
            'label': f'Expertise Level: {level}',
            'color': 'blue'
        })
        
        # Value badge
        avg_ltv = characteristics.get('avg_ltv', 0)
        badges.append({
            'icon': '💰',
            'label': f'Historic Value: ${int(avg_ltv)}',
            'color': 'green'
        })
        
        # Purchase frequency badge
        purchase_freq = characteristics.get('avg_purchase_frequency', 0)
        if purchase_freq > 10:
            badges.append({
                'icon': '🔄',
                'label': 'Frequent Buyers',
                'color': 'purple'
            })
        
        return badges[:3]  # Max 3 badges for display


# Singleton instance
_image_mapper = None

def get_image_mapper() -> ImageMapper:
    """Get singleton image mapper instance"""
    global _image_mapper
    if _image_mapper is None:
        _image_mapper = ImageMapper()
    return _image_mapper

