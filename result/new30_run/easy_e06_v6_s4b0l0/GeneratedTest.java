import org.openqa.selenium.*;
import org.openqa.selenium.interactions.Actions;
import java.util.Set;
import java.util.ArrayList;

public class GeneratedTest {
    public static void main(String[] args) {
        WebDriver driver = new ChromeDriver();
        Actions actions = new Actions(driver);

        driver.get("https://app.diagrams.net/");

        driver.findElement(By.xpath("//body/div[3]/div[1]/div[4]/div[1]/a[1]")).click();

        WebElement object1 = driver.findElement(By.cssSelector(".geDiagramContainer svg > g > g:nth-child(2) > g:nth-child(135)"));
        actions.doubleClick(object1).perform();

        actions.sendKeys("Nightly timer fires").perform();

        driver.findElement(By.xpath("//not-found")).click();

        WebElement object6 = driver.findElement(By.xpath("//not-found"));
        object6.click();
        Thread.sleep(500);
        for(int i=0; i<15; i++) { actions.keyDown(Keys.SHIFT).sendKeys(Keys.ARROW_DOWN).keyUp(Keys.SHIFT).perform(); }

        WebElement object11 = driver.findElement(By.xpath("//not-found"));
        object11.click();
        Thread.sleep(500);
        for(int i=0; i<15; i++) { actions.keyDown(Keys.SHIFT).sendKeys(Keys.ARROW_DOWN).keyUp(Keys.SHIFT).perform(); }

        WebElement object16 = driver.findElement(By.xpath("//not-found"));
        actions.doubleClick(object16).perform();

        actions.sendKeys("List changed files").perform();

        driver.findElement(By.xpath("//not-found")).click();

        WebElement object21 = driver.findElement(By.xpath("//not-found"));
        object21.click();
        Thread.sleep(500);
        for(int i=0; i<15; i++) { actions.keyDown(Keys.SHIFT).sendKeys(Keys.ARROW_DOWN).keyUp(Keys.SHIFT).perform(); }

        WebElement object26 = driver.findElement(By.xpath("//not-found"));
        object26.click();
        Thread.sleep(500);
        for(int i=0; i<15; i++) { actions.keyDown(Keys.SHIFT).sendKeys(Keys.ARROW_DOWN).keyUp(Keys.SHIFT).perform(); }

        WebElement object31 = driver.findElement(By.xpath("//not-found"));
        actions.doubleClick(object31).perform();

        actions.sendKeys("Compress the archive").perform();

        driver.findElement(By.xpath("//not-found")).click();

        WebElement object36 = driver.findElement(By.xpath("//not-found"));
        object36.click();
        Thread.sleep(500);
        for(int i=0; i<15; i++) { actions.keyDown(Keys.SHIFT).sendKeys(Keys.ARROW_DOWN).keyUp(Keys.SHIFT).perform(); }

        WebElement object41 = driver.findElement(By.xpath("//not-found"));
        object41.click();
        Thread.sleep(500);
        for(int i=0; i<15; i++) { actions.keyDown(Keys.SHIFT).sendKeys(Keys.ARROW_DOWN).keyUp(Keys.SHIFT).perform(); }

        WebElement object46 = driver.findElement(By.xpath("//not-found"));
        actions.doubleClick(object46).perform();

        actions.sendKeys("Backup complete").perform();

        WebElement object47 = driver.findElement(By.cssSelector(".geDiagramContainer svg > g > g:nth-child(2) > g:nth-child(135)"));
        WebElement relatedObject1 = driver.findElement(By.xpath("//not-found"));
        actions.moveToElement(object47, 0, object47.getSize().getHeight() / 2)
                .clickAndHold()
                .moveToElement(relatedObject1, 0, -relatedObject1.getSize().getHeight() / 2)
                .release()
                .perform();

        WebElement object48 = driver.findElement(By.xpath("//not-found"));
        WebElement relatedObject2 = driver.findElement(By.xpath("//not-found"));
        actions.moveToElement(object48, 0, object48.getSize().getHeight() / 2)
                .clickAndHold()
                .moveToElement(relatedObject2, 0, -relatedObject2.getSize().getHeight() / 2)
                .release()
                .perform();

        WebElement object49 = driver.findElement(By.xpath("//not-found"));
        WebElement relatedObject3 = driver.findElement(By.xpath("//not-found"));
        actions.moveToElement(object49, 0, object49.getSize().getHeight() / 2)
                .clickAndHold()
                .moveToElement(relatedObject3, 0, -relatedObject3.getSize().getHeight() / 2)
                .release()
                .perform();

        driver.quit();
    }
}