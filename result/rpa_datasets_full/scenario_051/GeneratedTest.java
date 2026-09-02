import org.openqa.selenium.*;
import org.openqa.selenium.interactions.Actions;
import java.util.Set;
import java.util.ArrayList;

public class GeneratedTest {
    public static void main(String[] args) {
        WebDriver driver = new ChromeDriver();
        Actions actions = new Actions(driver);

        driver.get("https://app.diagrams.net/");

        driver.findElement(By.xpath("//body/div[7]/div[1]/input[1]")).click();

        driver.findElement(By.xpath("/html/body/div[11]/table/tbody/tr[16]/td[2]")).click();

        driver.findElement(By.xpath("//body/div[3]/div[1]/div[4]/div[1]/a[1]")).click();

        WebElement object1 = driver.findElement(By.cssSelector(".geDiagramContainer svg > g > g:nth-child(2) > g:nth-child(58)"));
        object1.click();
        Thread.sleep(500);
        for(int i=0; i<15; i++) { actions.keyDown(Keys.SHIFT).sendKeys(Keys.ARROW_UP).keyUp(Keys.SHIFT).perform(); }

        WebElement object2 = driver.findElement(By.cssSelector(".geDiagramContainer svg > g > g:nth-child(2) > g:nth-child(58)"));
        object2.click();
        Thread.sleep(500);
        for(int i=0; i<15; i++) { actions.keyDown(Keys.SHIFT).sendKeys(Keys.ARROW_UP).keyUp(Keys.SHIFT).perform(); }

        WebElement object3 = driver.findElement(By.cssSelector(".geDiagramContainer svg > g > g:nth-child(2) > g:nth-child(58)"));
        object3.click();
        Thread.sleep(500);
        for(int i=0; i<15; i++) { actions.keyDown(Keys.SHIFT).sendKeys(Keys.ARROW_UP).keyUp(Keys.SHIFT).perform(); }

        WebElement object8 = driver.findElement(By.xpath("//not-found"));
        object8.click();
        Thread.sleep(500);
        for(int i=0; i<15; i++) { actions.keyDown(Keys.SHIFT).sendKeys(Keys.ARROW_LEFT).keyUp(Keys.SHIFT).perform(); }

        WebElement object13 = driver.findElement(By.xpath("//not-found"));
        object13.click();
        Thread.sleep(500);
        for(int i=0; i<30; i++) { actions.keyDown(Keys.CONTROL).sendKeys(Keys.ARROW_RIGHT).keyUp(Keys.CONTROL).perform(); }

        driver.findElement(By.xpath("//body/div[7]/div[1]/input[1]")).click();

        driver.findElement(By.xpath("/html/body/div[11]/table/tbody/tr[16]/td[2]")).click();

        WebElement object18 = driver.findElement(By.xpath("//not-found"));
        object18.click();
        Thread.sleep(500);
        for(int i=0; i<30; i++) { actions.keyDown(Keys.CONTROL).sendKeys(Keys.ARROW_DOWN).keyUp(Keys.CONTROL).perform(); }

        driver.findElement(By.xpath("//body/div[7]/div[1]/input[1]")).click();

        driver.findElement(By.xpath("/html/body/div[11]/table/tbody/tr[16]/td[2]")).click();

        driver.findElement(By.xpath("//body/div[3]/div[1]/div[4]/div[1]/a[25]")).click();

        WebElement object19 = driver.findElement(By.cssSelector(".geDiagramContainer svg > g > g:nth-child(2) > g:nth-child(60)"));
        object19.click();
        Thread.sleep(500);
        for(int i=0; i<15; i++) { actions.keyDown(Keys.SHIFT).sendKeys(Keys.ARROW_UP).keyUp(Keys.SHIFT).perform(); }

        WebElement object20 = driver.findElement(By.cssSelector(".geDiagramContainer svg > g > g:nth-child(2) > g:nth-child(60)"));
        object20.click();
        Thread.sleep(500);
        for(int i=0; i<15; i++) { actions.keyDown(Keys.SHIFT).sendKeys(Keys.ARROW_UP).keyUp(Keys.SHIFT).perform(); }

        WebElement object25 = driver.findElement(By.xpath("//not-found"));
        object25.click();
        Thread.sleep(500);
        for(int i=0; i<15; i++) { actions.keyDown(Keys.SHIFT).sendKeys(Keys.ARROW_LEFT).keyUp(Keys.SHIFT).perform(); }

        WebElement object30 = driver.findElement(By.xpath("//not-found"));
        object30.click();
        Thread.sleep(500);
        for(int i=0; i<15; i++) { actions.keyDown(Keys.SHIFT).sendKeys(Keys.ARROW_LEFT).keyUp(Keys.SHIFT).perform(); }

        driver.findElement(By.xpath("//body/div[7]/div[1]/input[1]")).click();

        driver.findElement(By.xpath("/html/body/div[11]/table/tbody/tr[16]/td[2]")).click();

        driver.findElement(By.xpath("//body/div[3]/div[1]/div[4]/div[1]/a[3]")).click();

        WebElement object35 = driver.findElement(By.xpath("//not-found"));
        object35.click();
        Thread.sleep(500);
        for(int i=0; i<15; i++) { actions.keyDown(Keys.SHIFT).sendKeys(Keys.ARROW_UP).keyUp(Keys.SHIFT).perform(); }

        WebElement object40 = driver.findElement(By.xpath("//not-found"));
        object40.click();
        Thread.sleep(500);
        for(int i=0; i<15; i++) { actions.keyDown(Keys.SHIFT).sendKeys(Keys.ARROW_UP).keyUp(Keys.SHIFT).perform(); }

        driver.findElement(By.xpath("//body/div[7]/div[1]/input[1]")).click();

        driver.findElement(By.xpath("/html/body/div[11]/table/tbody/tr[16]/td[2]")).click();

        driver.findElement(By.xpath("//body/div[3]/div[1]/div[4]/div[1]/a[1]")).click();

        WebElement object41 = driver.findElement(By.cssSelector(".geDiagramContainer svg > g > g:nth-child(2) > g:nth-child(65)"));
        object41.click();
        Thread.sleep(500);
        for(int i=0; i<15; i++) { actions.keyDown(Keys.SHIFT).sendKeys(Keys.ARROW_LEFT).keyUp(Keys.SHIFT).perform(); }

        WebElement object42 = driver.findElement(By.cssSelector(".geDiagramContainer svg > g > g:nth-child(2) > g:nth-child(60)"));
        WebElement relatedObject1 = driver.findElement(By.cssSelector(".geDiagramContainer svg > g > g:nth-child(2) > g:nth-child(65)"));
        actions.moveToElement(object42, 0, object42.getSize().getHeight() / 2)
                .clickAndHold()
                .moveToElement(relatedObject1, 0, -relatedObject1.getSize().getHeight() / 2)
                .release()
                .perform();

        driver.findElement(By.xpath("//body/div[7]/div[1]/input[1]")).click();

        driver.findElement(By.xpath("/html/body/div[11]/table/tbody/tr[16]/td[2]")).click();

        driver.findElement(By.xpath("//body/div[3]/div[1]/div[4]/div[1]/a[1]")).click();

        WebElement object47 = driver.findElement(By.xpath("//not-found"));
        object47.click();
        Thread.sleep(500);
        for(int i=0; i<15; i++) { actions.keyDown(Keys.SHIFT).sendKeys(Keys.ARROW_DOWN).keyUp(Keys.SHIFT).perform(); }

        WebElement object48 = driver.findElement(By.cssSelector(".geDiagramContainer svg > g > g:nth-child(2) > g:nth-child(61)"));
        WebElement relatedObject2 = driver.findElement(By.xpath("//not-found"));
        actions.moveToElement(object48, 0, object48.getSize().getHeight() / 2)
                .clickAndHold()
                .moveToElement(relatedObject2, 0, -relatedObject2.getSize().getHeight() / 2)
                .release()
                .perform();

        WebElement object49 = driver.findElement(By.cssSelector(".geDiagramContainer svg > g > g:nth-child(2) > g:nth-child(65)"));
        actions.doubleClick(object49).perform();

        WebElement textBox = driver.switchTo().activeElement();
        textBox.sendKeys("Test");

        WebElement object50 = driver.findElement(By.cssSelector(".geDiagramContainer svg > g > g:nth-child(2) > g:nth-child(66)"));
        actions.doubleClick(object50).perform();

        actions.sendKeys("Login").perform();

        WebElement object55 = driver.findElement(By.xpath("//not-found"));
        actions.doubleClick(object55).perform();

        actions.sendKeys("Register").perform();

        WebElement object60 = driver.findElement(By.xpath("//not-found"));
        object60.click();
        Thread.sleep(500);
        for(int i=0; i<15; i++) { actions.keyDown(Keys.SHIFT).sendKeys(Keys.ARROW_UP).keyUp(Keys.SHIFT).perform(); }

        WebElement object65 = driver.findElement(By.xpath("//not-found"));
        object65.click();
        Thread.sleep(500);
        for(int i=0; i<15; i++) { actions.keyDown(Keys.SHIFT).sendKeys(Keys.ARROW_UP).keyUp(Keys.SHIFT).perform(); }

        WebElement object70 = driver.findElement(By.xpath("//not-found"));
        object70.click();
        Thread.sleep(500);
        for(int i=0; i<15; i++) { actions.keyDown(Keys.SHIFT).sendKeys(Keys.ARROW_UP).keyUp(Keys.SHIFT).perform(); }

        driver.quit();
    }
}