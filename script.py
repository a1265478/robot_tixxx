
import random

SCRIPT = """ 
            Object.defineProperty(navigator, 'webdriver', {get: () => undefined});
            Object.defineProperty(navigator, 'plugins', {
                get: () => {
                    return [{
                        0: {type: "application/x-google-chrome-pdf"},
                        description: "Portable Document Format",
                        filename: "internal-pdf-viewer",
                        name: "Chrome PDF Plugin"
                    }];
                }
            });
            
            Object.defineProperty(navigator, 'languages', {
                get: () => ['zh-TW', 'zh', 'en-US', 'en']
            });
            
            
            delete window.cdc_adoQpoasnfa76pfcZLmcfl_Array;
            delete window.cdc_adoQpoasnfa76pfcZLmcfl_Promise;
            delete window.cdc_adoQpoasnfa76pfcZLmcfl_Symbol;
            
            const originalGetContext = HTMLCanvasElement.prototype.getContext;
            HTMLCanvasElement.prototype.getContext = function(type) {
                const context = originalGetContext.apply(this, arguments);
                if (type === '2d') {
                    const originalFillText = context.fillText;
                    context.fillText = function() {
                        arguments[0] = arguments[0] + ' ';
                        return originalFillText.apply(this, arguments);
                    }
                }
                return context;
            };
        """

BROWSER_ARGS = ['--disable-dev-shm-usage',
    '--no-sandbox',
    '--disable-blink-features=AutomationControlled',
    '--disable-automation',
    '--disable-infobars',
    '--disable-blink-features',
    '--disable-blink-features=AutomationControlled',
    f'--window-size={random.randint(1050, 1200)},{random.randint(800, 900)}',
    '--disable-gpu',
]