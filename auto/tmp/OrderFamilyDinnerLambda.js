exports.handler = async (event) => {
    console.log('Received event:', JSON.stringify(event, null, 2));
    
    const intent = event.currentIntent;
    const slots = intent.slots;
    
    const numberOfPeople = parseInt(slots.NumberOfPeople);
    const familyDinnerStyle = slots.FamilyDinnerStyle;
    
    // Validate minimum people requirement
    if (numberOfPeople < 2) {
        return {
            dialogAction: {
                type: 'ElicitSlot',
                intentName: intent.name,
                slots: slots,
                slotToElicit: 'NumberOfPeople',
                message: {
                    contentType: 'PlainText',
                    content: 'Family dinners require a minimum of 2 people. How many people will be dining?'
                }
            }
        };
    }
    
    // Define menu configurations
    const familyDinnerMenus = {
        'Hong Kong style': {
            pricePerPerson: 14.75,
            baseDishes: [
                'Spring Egg Rolls',
                'Minced Beef with Egg White Soup',
                'Beef with Broccoli',
                'Shrimp with Mixed Vegetables',
                'Barbecued Pork Fried Rice'
            ],
            additionalDishes: {
                3: 'Succulent Spicy Pork with Garlic Sauce',
                4: 'Clams with Black Bean Sauce',
                5: 'Braised Fish Fillet',
                6: 'Double Mushroom with Oyster Sauce'
            }
        },
        'Peking style': {
            pricePerPerson: 15.75,
            baseDishes: [
                'Golden Pot Stickers',
                'Hot & Sour Soup',
                'Mongolian Beef',
                'Kung Pao Shrimp',
                'Yang Chow Fried Rice'
            ],
            additionalDishes: {
                3: 'Spicy Hot Bean Curd with Minced Pork',
                4: 'Squids with Green Onion',
                5: 'Sliced Rock Cod with Special Sauce',
                6: 'Snow Pea with Mushroom'
            }
        }
    };
    
    // Get the selected menu
    const selectedMenu = familyDinnerMenus[familyDinnerStyle];
    
    if (!selectedMenu) {
        return {
            dialogAction: {
                type: 'ElicitSlot',
                intentName: intent.name,
                slots: slots,
                slotToElicit: 'FamilyDinnerStyle',
                message: {
                    contentType: 'PlainText',
                    content: 'Would you prefer the Hong Kong style or Peking style family dinner?'
                }
            }
        };
    }
    
    // Calculate total price
    const totalPrice = (selectedMenu.pricePerPerson * numberOfPeople).toFixed(2);
    
    // Build the list of included dishes
    let includedDishes = [...selectedMenu.baseDishes];
    
    // Add additional dishes based on party size
    for (let i = 3; i <= Math.min(numberOfPeople, 6); i++) {
        if (selectedMenu.additionalDishes[i]) {
            includedDishes.push(selectedMenu.additionalDishes[i]);
        }
    }
    
    // Format the response
    const dishList = includedDishes.map((dish, index) => `${index + 1}. ${dish}`).join('\\n');
    
    // Return fulfillment
    return {
        dialogAction: {
            type: 'Close',
            fulfillmentState: 'Fulfilled',
            message: {
                contentType: 'PlainText',
                content: `Perfect! I've placed your order for a ${familyDinnerStyle} family dinner for ${numberOfPeople} people.

Total Price: $${totalPrice}

Your dinner includes:
${dishList}

Your order will be ready in approximately 25-30 minutes.`
            }
        },
        sessionAttributes: {
            orderType: 'familyDinner',
            style: familyDinnerStyle,
            numberOfPeople: numberOfPeople.toString(),
            totalPrice: totalPrice,
            dishes: JSON.stringify(includedDishes)
        }
    };
};